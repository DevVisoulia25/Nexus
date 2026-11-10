"""Small temporal-convolution candidate, optional PyTorch training dependency.

R005 changes the classifier architecture relative to R004. Identical active
windows and training-fitted standardization; fixed epochs, no dev early stop.
Candidate weights never replace the running app automatically.
"""
import argparse
import hashlib
import json
import random
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

from nexus.features import POINTS, active_sequence, sequence_vector
from nexus.replay import evaluate, load_samples


class TemporalNet(nn.Module):
    def __init__(self, classes):
        super().__init__()
        self.layers = nn.Sequential(nn.Conv1d(POINTS * 3, 32, 3, padding=1), nn.ReLU(),
                                    nn.Conv1d(32, 32, 3, padding=1), nn.ReLU(),
                                    nn.AdaptiveAvgPool1d(1), nn.Flatten(), nn.Linear(32, classes))

    def forward(self, x):
        return self.layers(x.transpose(1, 2))


class TemporalModel:
    def __init__(self, path):
        with np.load(path, allow_pickle=False) as data:
            self.metadata = json.loads(str(data["metadata"]))
            self.classes = data["classes"].tolist()
            self.mean, self.scale = data["mean"], data["scale"]
            self.net = TemporalNet(len(self.classes))
            state = {name: torch.from_numpy(data["weight_" + name].copy()) for name in self.net.state_dict()}
        self.net.load_state_dict(state, strict=True)
        self.net.eval()

    def predict(self, frames, timestamps):
        steps = self.metadata["steps"]
        size = steps * POINTS * 3
        vector = sequence_vector(*active_sequence(frames, timestamps), steps)[:size]
        x = ((vector - self.mean) / self.scale).reshape(steps, POINTS * 3)
        with torch.inference_mode():
            scores = self.net(torch.from_numpy(x.astype(np.float32))[None])[0].numpy()
        order = np.argsort(scores)[::-1]
        margin = float(scores[order[0]] - scores[order[1]])
        accepted = margin >= self.metadata["rejection_margin"]
        return {"candidate": self.classes[order[0]], "label": self.classes[order[0]] if accepted else None,
                "accepted": accepted, "margin": margin}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    if not 1 <= args.epochs <= 100:
        raise ValueError("Experiment cap is 100 epochs")
    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable; explicitly select cpu or obtain a free GPU runtime")
    torch.set_num_threads(2)
    random.seed(20261107)
    np.random.seed(20261107)
    torch.manual_seed(20261107)
    torch.use_deterministic_algorithms(True)
    started = time.perf_counter()
    samples, manifest_hash = load_samples()
    baseline_path = Path("models/signs-active-candidate.npz")
    with np.load(baseline_path, allow_pickle=False) as baseline:
        metadata = json.loads(str(baseline["metadata"]))
        if metadata["manifest_sha256"] != manifest_hash:
            raise ValueError("Run R004 with this manifest before R005")
        steps = metadata["steps"]
        size = steps * POINTS * 3
        mean, scale = baseline["mean"][:size], baseline["scale"][:size]
        classes = baseline["classes"]
    vectors = np.array([sequence_vector(*active_sequence(f, t), steps)[:size] for _, f, t in samples])
    x = ((vectors - mean) / scale).reshape(-1, steps, POINTS * 3).astype(np.float32)
    labels = np.array([s["label"] for s, _, _ in samples])
    train = np.array([s["split"] == "train" for s, _, _ in samples])
    known = np.array([s["split"] == "val" and s["role"] == "known" for s, _, _ in samples])
    unknown = np.array([s["role"] == "unknown" for s, _, _ in samples])
    y = np.array([list(classes).index(label) for label in labels[train]])
    train_x = torch.from_numpy(x[train]).to(args.device)
    train_y = torch.from_numpy(y).long().to(args.device)
    net = TemporalNet(len(classes)).to(args.device)
    counts = np.bincount(y, minlength=len(classes))
    weights = torch.tensor(len(y) / (len(classes) * counts), dtype=torch.float32, device=args.device)
    loss_fn = nn.CrossEntropyLoss(weight=weights)
    optimizer = torch.optim.AdamW(net.parameters(), lr=.001, weight_decay=.001)
    losses = []
    for epoch in range(args.epochs):
        net.train()
        permutation = torch.randperm(len(y), device=args.device)
        total = 0.
        for indices in permutation.split(32):
            optimizer.zero_grad()
            loss = loss_fn(net(train_x[indices]), train_y[indices])
            loss.backward()
            optimizer.step()
            total += float(loss.detach().cpu()) * len(indices)
        losses.append(total / len(y))
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{args.epochs}; train loss {losses[-1]:.4f}", flush=True)
    net.eval()
    with torch.inference_mode():
        scores = net(torch.from_numpy(x).to(args.device)).cpu().numpy()
    sorted_scores = np.sort(scores, axis=1)
    # Compare in float64 so nextafter's strict calibration boundary is not
    # rounded back to a float32 observed score by NumPy scalar promotion.
    margins = (sorted_scores[:, -1] - sorted_scores[:, -2]).astype(np.float64)
    threshold = float(np.nextafter(np.quantile(margins[unknown], .9, method="higher"), np.inf))
    predictions = classes[scores.argmax(1)]
    accepted = margins >= threshold
    metadata.update(model_kind="temporal_conv", experiment="R005", rejection_margin=threshold,
                    epochs=args.epochs, training_device=args.device, torch_version=torch.__version__)
    output = Path("models/signs-temporal-candidate.npz")
    weights = {"weight_" + name: value.detach().cpu().numpy() for name, value in net.state_dict().items()}
    np.savez_compressed(output, mean=mean, scale=scale, classes=classes, metadata=json.dumps(metadata), **weights)
    restored = TemporalModel(output)
    restored_candidates = [restored.predict(f, t)["candidate"] for _, f, t in samples]
    if not np.array_equal(restored_candidates, predictions):
        raise RuntimeError("Export/reload parity failed")
    policy = {"min_seconds": .25, "min_frames": 3, "finalize_on_release": True}
    replay_summary, rows = evaluate(restored, samples, policy)
    timings = []
    for _, frames, times in samples[:20]:
        start = time.perf_counter()
        restored.predict(frames, times)
        timings.append((time.perf_counter() - start) * 1000)
    report = {"experiment": "R005", "epochs": args.epochs, "seed": 20261107,
              "device": args.device, "torch_version": torch.__version__, "manifest_sha256": manifest_hash,
              "baseline_model_sha256": hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
              "parameters": sum(p.numel() for p in net.parameters()), "model_bytes": output.stat().st_size,
              "whole_clip_correct": int((predictions[known] == labels[known]).sum()), "known_clips": int(known.sum()),
              "known_correct_accepted": int(((predictions == labels) & accepted & known).sum()),
              "unknown_calibration_rejected": int((~accepted[unknown]).sum()),
              "replay": replay_summary, "train_loss": losses, "wall_s": time.perf_counter() - started,
              "cpu_classifier_ms_p50": float(np.median(timings)), "cpu_classifier_ms_p95": float(np.percentile(timings, 95)),
              "export_reload_prediction_parity": True, "promoted": False, "test_evaluated": False,
              "limitations": ["Previously observed small development/calibration set", "No webcam validation",
                              "Classifier timing excludes landmark extraction", "No ordinary-movement negatives",
                              "Temporal network uses only supplied windows; this is not sentence translation"]}
    Path("artifacts/recognition/temporal_experiment.json").write_text(json.dumps(report, indent=2))
    Path("artifacts/recognition/private/temporal_clips.json").write_text(json.dumps(rows, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "train_loss"}, indent=2))


if __name__ == "__main__":
    main()
