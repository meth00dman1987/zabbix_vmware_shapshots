#!/usr/bin/env python3
import sys
import json
import re
import ssl
from datetime import datetime, timezone

from pyVim import connect
from pyVmomi import vim


def iter_snapshot_tree(snapshot_tree):
    """Yield (name, createTime) for every snapshot in the tree."""
    stack = list(snapshot_tree or [])
    while stack:
        node = stack.pop()
        # node: vim.vm.SnapshotTree
        yield node.name, node.createTime
        if node.childSnapshotList:
            stack.extend(list(node.childSnapshotList))


def get_all_vms(content):
    view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
    try:
        return list(view.view)
    finally:
        view.Destroy()


def main():
    # Args: vcenter_host user pass age_hours exclude_vm_regex
    if len(sys.argv) < 5:
        print(json.dumps({"error": "Usage: vmware_old_snapshots.py <vcenter> <user> <pass> <age_hours> [exclude_vm_regex]"}))
        return 2

    vcenter = sys.argv[1]
    user = sys.argv[2]
    password = sys.argv[3]
    try:
        age_hours = int(sys.argv[4])
    except ValueError:
        print(json.dumps({"error": "age_hours must be integer"}))
        return 2

    exclude_vm_regex = sys.argv[5] if len(sys.argv) >= 6 else ""
    exclude_re = re.compile(exclude_vm_regex) if exclude_vm_regex else None

    # Disable SSL verify (common in vCenter with self-signed certs)
    context = ssl._create_unverified_context()

    si = None
    try:
        si = connect.SmartConnect(host=vcenter, user=user, pwd=password, sslContext=context)
        content = si.RetrieveContent()

        now = datetime.now(timezone.utc)
        threshold_seconds = age_hours * 3600

        snapshots = []
        for vm in get_all_vms(content):
            vm_name = getattr(vm, "name", None) or ""
            if exclude_re and exclude_re.search(vm_name):
                continue

            # Skip templates and powered-off? (не обязательно). Оставим все VM как есть.
            if not hasattr(vm, "snapshot") or vm.snapshot is None:
                continue

            # vm.snapshot.rootSnapshotList is snapshot tree
            root = vm.snapshot.rootSnapshotList
            for snap_name, created in iter_snapshot_tree(root):
                # created may be naive or aware; normalize to aware UTC
                if created.tzinfo is None:
                    created_utc = created.replace(tzinfo=timezone.utc)
                else:
                    created_utc = created.astimezone(timezone.utc)

                age_sec = (now - created_utc).total_seconds()
                if age_sec >= threshold_seconds:
                    snapshots.append({
                        "vm": vm_name,
                        "snapshot": snap_name,
                        "created_utc": created_utc.isoformat(),
                        "age_hours": round(age_sec / 3600.0, 2)
                    })

        # Sort: oldest first
        snapshots.sort(key=lambda x: x["age_hours"], reverse=True)

        out = {
            "count": len(snapshots),
            "age_hours_threshold": age_hours,
            "exclude_vm_regex": exclude_vm_regex,
            "snapshots": snapshots
        }

        print(json.dumps(out, ensure_ascii=False))
        return 0

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        return 1

    finally:
        if si:
            try:
                connect.Disconnect(si)
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(main())