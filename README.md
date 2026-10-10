# Cloud Computing Research Project

This repository contains the code, Kubernetes manifests, and reproduction steps for a fault-tolerant edge-state synchronization experiment using k3d, Docker Desktop, and Chaos Mesh.

## Project goal

The project compares a static 30-second synchronization policy with a telemetry-driven adaptive scheduler to reduce state loss under node failure.

## Included files

- `adaptive_sync.py` — telemetry-driven adaptive sync controller
- `adaptive_deploy.yaml` — deployment for adaptive scheduling
- `app.py` — baseline state generator
- `sync.sh` — baseline static sync worker
- `baseline-deploy.yaml` — baseline deployment
- `fault-injection.yaml` — Chaos Mesh fault schedule

## Verification results

| Configuration | Sync interval | Data loss |
| --- | --- | --- |
| Reproduced baseline | 30s fixed | 14.77% |
| Adaptive scheduler | 0.1s–0.5s dynamic | 0.83% |

Reduction in state loss:

- 14.77% to 0.83%
- Improvement: approximately 94.4%

## Data loss formula

```text
Data Loss (%) = ((Generated - Synced) / Generated) * 100
```

## Prerequisites

- Windows 10/11
- Docker Desktop
- PowerShell
- k3d
- kubectl
- Helm
- Git

## Setup commands

### 1) Start the cluster

```powershell
k3d cluster create edge-testbed --agents 2
```

### 2) Install Chaos Mesh by Helm

```powershell
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm repo update
kubectl create namespace chaos-mesh --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install chaos-mesh chaos-mesh/chaos-mesh --namespace chaos-mesh --version 2.8.4 --set chaosDaemon.runtime=containerd --set chaosDaemon.socketPath=/run/k3s/containerd/containerd.sock --set controllerManager.replicaCount=1
```

### 3) Configure the baseline workload

From the project root:

```powershell
kubectl create configmap app-script --from-file=app.py --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap sync-script --from-file=sync.sh --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f baseline-deploy.yaml
```

### 4) Trigger the baseline experiment

```powershell
kubectl apply -f fault-injection.yaml
```

### 5) Extract baseline metrics

```powershell
kubectl exec deploy/primary-node -c state-generator -- tail -n 1 /data/state_journal.log
kubectl exec deploy/primary-node -c sync-agent -- tail -n 1 /shared-volume/synced_state.log
```

If the kubelet exec tunnel fails in k3d, use the Docker fallback:

```powershell
$node = kubectl get pods -l app=edge-primary -o jsonpath='{.items[0].spec.nodeName}'
docker exec $node sh -c "tail -n 1 /var/lib/rancher/k3s/storage/pvc-*/state_journal.log"
docker exec $node sh -c "tail -n 1 /var/lib/rancher/k3s/storage/pvc-*/synced_state.log"
```

## Adaptive experiment

### 1) Apply the adaptive controller

From the project root:

```powershell
kubectl create configmap adaptive-script --from-file=adaptive_sync.py --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f adaptive_deploy.yaml
kubectl apply -f fault-injection.yaml
```

### 2) Watch the adaptive synchronization logic

```powershell
$pod = kubectl get pods -l app=edge-primary --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}'
kubectl logs $pod -c sync-agent -f
```

### 3) Re-run metric extraction after the next failure

```powershell
kubectl exec deploy/primary-node -c state-generator -- tail -n 1 /data/state_journal.log
kubectl exec deploy/primary-node -c sync-agent -- tail -n 1 /shared-volume/synced_state.log
```

## Methodological summary

The baseline workload writes state updates to a journal at a fixed 30-second synchronization interval. The adaptive controller measures the current data-generation rate and computes the next synchronization interval using the online optimization rule encoded in `adaptive_sync.py`. This policy reduces the sync interval during high-rate generation and relaxes it during low-rate periods. Under Chaos Mesh-induced pod-kill conditions, this reduces state loss substantially compared with the static baseline policy.

## Repository purpose

This repository documents the implementation and empirical validation of a telemetry-driven adaptive synchronization controller for edge-state replication under fault conditions.
