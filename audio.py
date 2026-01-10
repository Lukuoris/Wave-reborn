import subprocess
import time
import sys
import config

# Load configuration
CHANNELS = config.get_channels()
LATENCY_MS = config.get_latency()

OBS_SINKS = {}        # Channel sinks (applications route here, always at 100%)
OBS_VIRTUAL_SINKS = {}  # Virtual sinks for OBS recording (one per channel)
LOOPBACK_STREAM_MODULE_IDS = {}  # Loopback module IDs: channel -> module_id (for OBS)
LOOPBACK_MONITOR_MODULE_IDS = {}  # Loopback module IDs: channel -> module_id (for monitor)
STREAM_SINK_INPUT_INDICES = {}  # Sink input indices for OBS loopbacks: channel -> index
MONITOR_SINK_INPUT_INDICES = {}  # Sink input indices on monitor sink: channel -> index

VOLUME_STREAM_STATE = {}  # Stream fader (controls sink-input-volume on stream sink)
VOLUME_YOU_STATE = {}     # Monitor fader (controls sink-input-volume on monitor sink)
MUTE_STATE = {}

# Your audio card for local monitoring (configurable)
SINK_OUTPUT_DEVICE = config.get_audio_output_device()

def check_pulseaudio():
    """Check if PulseAudio is running"""
    try:
        result = subprocess.run(["pactl", "info"],
                              capture_output=True,
                              text=True,
                              timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def init_audio():
    # Check if PulseAudio is available
    if not check_pulseaudio():
        print("ERROR: PulseAudio is not running or pactl is not installed!", file=sys.stderr)
        print("Please install PulseAudio and ensure it's running.", file=sys.stderr)
        return False

    cleanup_modules()

    # Create channel sinks (for applications)
    for ch in CHANNELS:
        app_sink_name = f"{ch}_Apps"
        subprocess.run([
            "pactl", "load-module", "module-null-sink",
            f"sink_name={app_sink_name}", f"sink_properties=device.description={ch}_Applications"
        ], check=False)
        OBS_SINKS[ch] = app_sink_name
        # Keep at 100% - applications control their own volume
        subprocess.run(["pactl", "set-sink-volume", app_sink_name, "100%"], check=False)

    time.sleep(0.2)

    # Create virtual sinks for OBS (one per channel)
    for ch in CHANNELS:
        obs_sink_name = f"{ch}_OBS"
        subprocess.run([
            "pactl", "load-module", "module-null-sink",
            f"sink_name={obs_sink_name}", f"sink_properties=device.description={ch}_OBS"
        ], check=False)
        OBS_VIRTUAL_SINKS[ch] = obs_sink_name
        VOLUME_STREAM_STATE[ch] = 100
        VOLUME_YOU_STATE[ch] = 100
        MUTE_STATE[ch] = False

    time.sleep(0.3)

    # Set all OBS virtual sinks to 100% after they're created
    for ch in CHANNELS:
        obs_sink_name = OBS_VIRTUAL_SINKS[ch]
        subprocess.run(["pactl", "set-sink-volume", obs_sink_name, "100%"], check=False)

    time.sleep(0.2)

    # Create loopbacks: Apps monitor -> OBS virtual sink (controlled by Stream fader)
    # and Apps monitor -> Headphones (controlled by Monitor fader)
    for ch in CHANNELS:
        app_sink_name = OBS_SINKS[ch]
        monitor_source = f"{app_sink_name}.monitor"
        obs_virtual_sink = OBS_VIRTUAL_SINKS[ch]

        # Loopback: channel monitor -> OBS virtual sink (for recording)
        proc = subprocess.run([
            "pactl", "load-module", "module-loopback",
            f"source={monitor_source}",
            f"sink={obs_virtual_sink}",
            f"latency_msec={LATENCY_MS}"
        ], capture_output=True, text=True)
        if proc.stdout.strip():
            LOOPBACK_STREAM_MODULE_IDS[ch] = proc.stdout.strip()

        # Loopback: channel monitor -> headphones (for monitoring)
        proc = subprocess.run([
            "pactl", "load-module", "module-loopback",
            f"source={monitor_source}",
            f"sink={SINK_OUTPUT_DEVICE}",
            f"latency_msec={LATENCY_MS}"
        ], capture_output=True, text=True)
        if proc.stdout.strip():
            LOOPBACK_MONITOR_MODULE_IDS[ch] = proc.stdout.strip()

    time.sleep(0.5)

    # Find and store the sink-input indices using module IDs
    _refresh_indices()

    # Set all loopbacks to 100% volume initially
    for ch in CHANNELS:
        stream_idx = STREAM_SINK_INPUT_INDICES.get(ch)
        monitor_idx = MONITOR_SINK_INPUT_INDICES.get(ch)

        if stream_idx:
            subprocess.run(["pactl", "set-sink-input-volume", stream_idx, "100%"], check=False)
        if monitor_idx:
            subprocess.run(["pactl", "set-sink-input-volume", monitor_idx, "100%"], check=False)

    # Final check: ensure all OBS sinks are at 100% (PipeWire may restore old settings)
    time.sleep(0.1)
    for ch in CHANNELS:
        obs_sink_name = OBS_VIRTUAL_SINKS[ch]
        subprocess.run(["pactl", "set-sink-volume", obs_sink_name, "100%"], check=False)

    return True

def _refresh_indices():
    """Refresh sink-input indices by matching module IDs"""
    STREAM_SINK_INPUT_INDICES.clear()
    MONITOR_SINK_INPUT_INDICES.clear()

    # Get all sink inputs in detailed format
    res = subprocess.run(["pactl", "list", "sink-inputs"], capture_output=True, text=True)
    output = res.stdout

    # Split into sections for each sink input
    sections = output.split("Sink Input #")

    for section in sections[1:]:  # Skip first empty split
        # Get the index (first line)
        lines = section.split('\n')
        if not lines:
            continue
        idx = lines[0].strip().split()[0] if lines[0].strip() else None
        if not idx:
            continue

        # Get module ID from Properties
        module_id = None
        for line in section.split('\n'):
            if 'pulse.module.id' in line:
                try:
                    module_id = line.split('pulse.module.id = "')[1].split('"')[0]
                except (IndexError, ValueError):
                    pass
                break

        if not module_id:
            continue

        # Check which sink this goes to
        sink_name = None
        for line in section.split('\n'):
            if 'target.object = "' in line:
                try:
                    sink_name = line.split('target.object = "')[1].split('"')[0]
                except (IndexError, ValueError):
                    pass
                break

        # Match module ID to channels
        for ch in CHANNELS:
            stream_mod_id = LOOPBACK_STREAM_MODULE_IDS.get(ch)
            monitor_mod_id = LOOPBACK_MONITOR_MODULE_IDS.get(ch)

            # Check for stream loopback (goes to OBS virtual sink)
            if stream_mod_id and module_id == stream_mod_id:
                obs_virtual_sink = OBS_VIRTUAL_SINKS.get(ch)
                if obs_virtual_sink and obs_virtual_sink in sink_name:
                    STREAM_SINK_INPUT_INDICES[ch] = idx

            # Check for monitor loopback (goes to headphones)
            if monitor_mod_id and module_id == monitor_mod_id:
                if SINK_OUTPUT_DEVICE in sink_name:
                    MONITOR_SINK_INPUT_INDICES[ch] = idx

def cleanup_modules():
    # Clean up loopbacks
    res = subprocess.run(["pactl", "list", "short", "modules"], capture_output=True, text=True)
    for line in res.stdout.strip().split("\n"):
        if line and "module-loopback" in line:
            parts = line.split("\t")
            if len(parts) > 0:
                idx = parts[0]
                subprocess.run(["pactl", "unload-module", idx], check=False)

    # Clean up null sinks (including stream sink)
    res = subprocess.run(["pactl", "list", "short", "modules"], capture_output=True, text=True)
    for line in res.stdout.strip().split("\n"):
        if line and "module-null-sink" in line:
            parts = line.split("\t")
            if len(parts) > 0:
                idx = parts[0]
                subprocess.run(["pactl", "unload-module", idx], check=False)

# -------------------
# Volume control functions
# -------------------
def set_volume_stream(channel, value: int):
    """Stream fader - controls loopback volume to OBS virtual sink (affects OBS recording only)"""
    VOLUME_STREAM_STATE[channel] = value
    idx = STREAM_SINK_INPUT_INDICES.get(channel)
    if not idx:
        _refresh_indices()
        idx = STREAM_SINK_INPUT_INDICES.get(channel)

    if idx:
        subprocess.run(["pactl", "set-sink-input-volume", idx, f"{value}%"], check=False)

def set_volume_you(channel, value: int):
    """Monitor fader - controls sink-input-volume on headphones"""
    VOLUME_YOU_STATE[channel] = value
    idx = MONITOR_SINK_INPUT_INDICES.get(channel)
    if not idx:
        _refresh_indices()
        idx = MONITOR_SINK_INPUT_INDICES.get(channel)
    
    if idx:
        subprocess.run(["pactl", "set-sink-input-volume", idx, f"{value}%"], check=False)

def mute_channel(channel):
    """Mute both stream (OBS loopback) and monitor (headphones loopback)"""
    MUTE_STATE[channel] = True

    # Mute the OBS loopback
    stream_idx = STREAM_SINK_INPUT_INDICES.get(channel)
    if not stream_idx:
        _refresh_indices()
        stream_idx = STREAM_SINK_INPUT_INDICES.get(channel)
    if stream_idx:
        subprocess.run(["pactl", "set-sink-input-mute", stream_idx, "1"], check=False)

    # Mute the monitor loopback (affects headphones)
    monitor_idx = MONITOR_SINK_INPUT_INDICES.get(channel)
    if not monitor_idx:
        _refresh_indices()
        monitor_idx = MONITOR_SINK_INPUT_INDICES.get(channel)
    if monitor_idx:
        subprocess.run(["pactl", "set-sink-input-mute", monitor_idx, "1"], check=False)

def unmute_channel(channel):
    """Unmute both stream (OBS loopback) and monitor (headphones loopback)"""
    MUTE_STATE[channel] = False

    # Unmute the OBS loopback
    stream_idx = STREAM_SINK_INPUT_INDICES.get(channel)
    if not stream_idx:
        _refresh_indices()
        stream_idx = STREAM_SINK_INPUT_INDICES.get(channel)
    if stream_idx:
        subprocess.run(["pactl", "set-sink-input-mute", stream_idx, "0"], check=False)

    # Unmute the monitor loopback (affects headphones)
    monitor_idx = MONITOR_SINK_INPUT_INDICES.get(channel)
    if not monitor_idx:
        _refresh_indices()
        monitor_idx = MONITOR_SINK_INPUT_INDICES.get(channel)
    if monitor_idx:
        subprocess.run(["pactl", "set-sink-input-mute", monitor_idx, "0"], check=False)

# -------------------
# Application routing functions
# -------------------
def _get_smart_display_name(app_name, media_name, binary_name, process_id):
    """
    Smart logic to determine the best display name for an application

    Priority:
    1. Binary name (Discord, Steam, etc.) - most reliable
    2. Application name if it's meaningful
    3. Media name with truncation for long names
    4. Fallback to app_name
    """
    # Skip generic/unhelpful names
    unhelpful_names = [
        'playStream',
        'AudioStream',
        'output',
        'WEBRTC VoiceEngine',
        'AudioCallbackDriver',
        'libcanberra',
        'System Sounds'
    ]

    # If we have a binary name, use it (most reliable)
    if binary_name:
        # Clean up binary name
        clean_binary = binary_name

        # Remove common suffixes
        for suffix in ['-bin', '.bin', '.exe']:
            if clean_binary.endswith(suffix):
                clean_binary = clean_binary[:-len(suffix)]

        # Capitalize first letter
        clean_binary = clean_binary.capitalize()

        # Special cases - map known binaries to friendly names
        binary_mapping = {
            'zen': 'Zen Browser',
            'firefox': 'Firefox',
            'chrome': 'Chrome',
            'chromium': 'Chromium',
            'discord': 'Discord',
            'spotify': 'Spotify',
            'steam': 'Steam',
            'vlc': 'VLC Media Player',
            'mpv': 'MPV',
            'obs': 'OBS Studio',
            'pavucontrol': 'PulseAudio Volume Control',
            'telegram': 'Telegram',
            'slack': 'Slack',
            'teams': 'Microsoft Teams',
            'zoom': 'Zoom',
            'skype': 'Skype'
        }

        if clean_binary.lower() in binary_mapping:
            display = binary_mapping[clean_binary.lower()]
        else:
            display = clean_binary

        # For browsers, add media name (tab title) if available and meaningful
        browser_binaries = ['zen', 'firefox', 'chrome', 'chromium', 'opera', 'brave', 'vivaldi', 'edge']
        if clean_binary.lower() in browser_binaries and media_name and media_name not in unhelpful_names:
            # Truncate long tab titles
            max_tab_length = 50
            tab_title = media_name
            if len(tab_title) > max_tab_length:
                tab_title = tab_title[:max_tab_length] + "..."
            display = f"{display}: {tab_title}"
        # For non-browsers, just add process ID
        elif process_id:
            display = f"{display} (PID: {process_id})"

        return display

    # If app_name is meaningful and not generic
    if app_name and app_name not in unhelpful_names:
        return app_name

    # Use media_name but truncate if too long (like YouTube titles)
    if media_name and media_name not in unhelpful_names:
        # Truncate long media names (e.g., YouTube video titles)
        max_length = 60
        if len(media_name) > max_length:
            return media_name[:max_length] + "..."
        return media_name

    # Final fallback
    return app_name or "Unknown Application"

def get_applications():
    """Get list of all applications (sink-inputs) with their info"""
    apps = []
    res = subprocess.run(["pactl", "list", "sink-inputs"], capture_output=True, text=True)
    output = res.stdout
    
    # Get sink name mapping
    sink_map = {}
    sink_res = subprocess.run(["pactl", "list", "short", "sinks"], capture_output=True, text=True)
    for line in sink_res.stdout.strip().split('\n'):
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) >= 2:
            sink_idx = parts[0].strip()
            sink_name = parts[1].strip()
            sink_map[sink_idx] = sink_name
    
    sections = output.split("Sink Input #")
    for section in sections[1:]:
        lines = section.split('\n')
        if not lines:
            continue
        idx = lines[0].strip().split()[0] if lines[0].strip() else None
        if not idx:
            continue

        app_name = None
        media_name = None
        binary_name = None
        process_id = None
        sink_idx = None
        sink_name = None
        volume = 100

        for line in section.split('\n'):
            if 'application.name = "' in line:
                try:
                    app_name = line.split('application.name = "')[1].split('"')[0]
                except (IndexError, ValueError):
                    pass
            elif 'media.name = "' in line:
                try:
                    media_name = line.split('media.name = "')[1].split('"')[0]
                except (IndexError, ValueError):
                    pass
            elif 'application.process.binary = "' in line:
                try:
                    binary_name = line.split('application.process.binary = "')[1].split('"')[0]
                except (IndexError, ValueError):
                    pass
            elif 'application.process.id = "' in line:
                try:
                    process_id = line.split('application.process.id = "')[1].split('"')[0]
                except (IndexError, ValueError):
                    pass
            elif line.strip().startswith('Sink:'):
                try:
                    sink_idx = line.split('Sink:')[1].strip().split()[0]
                    sink_name = sink_map.get(sink_idx, 'Unknown')
                except (IndexError, ValueError):
                    pass
            elif 'Volume:' in line and 'front-left:' in line:
                try:
                    # Extract volume percentage
                    vol_part = line.split('front-left:')[1].split('/')[1].strip().replace('%', '')
                    volume = int(float(vol_part))
                except (IndexError, ValueError):
                    pass

        if app_name:  # Only include applications with names (exclude loopbacks)
            # Determine which channel this is on
            channel = None
            for ch in CHANNELS:
                if OBS_SINKS[ch] == sink_name:
                    channel = ch
                    break

            # Smart display name logic
            display_name = _get_smart_display_name(app_name, media_name, binary_name, process_id)

            apps.append({
                "index": idx,
                "name": display_name,
                "application": app_name,
                "binary": binary_name,
                "sink": sink_name,
                "current_channel": channel,
                "volume": volume
            })
    
    return apps

def route_application_to_channel(app_index: str, channel: str):
    """Route an application (sink-input) to a channel sink and persist the setting"""
    if channel not in CHANNELS:
        return False

    sink_name = OBS_SINKS[channel]

    # First, try to move using pactl
    result = subprocess.run(
        ["pactl", "move-sink-input", app_index, sink_name],
        capture_output=True, text=True
    )

    # Check if move was successful
    time.sleep(0.2)  # Small delay to let the system process the move

    # Verify the move by checking current sink
    check_res = subprocess.run(
        ["pactl", "list", "sink-inputs"],
        capture_output=True, text=True
    )

    moved_successfully = False
    for section in check_res.stdout.split("Sink Input #"):
        if section.startswith(app_index):
            for line in section.split('\n'):
                if line.strip().startswith('Sink:'):
                    # Get current sink index
                    try:
                        current_sink_idx = line.split('Sink:')[1].strip().split()[0]
                        # Get sink name for this index
                        sink_res = subprocess.run(
                            ["pactl", "list", "short", "sinks"],
                            capture_output=True, text=True
                        )
                        for sink_line in sink_res.stdout.strip().split('\n'):
                            parts = sink_line.split('\t')
                            if len(parts) >= 2 and parts[0].strip() == current_sink_idx:
                                if parts[1].strip() == sink_name:
                                    moved_successfully = True
                                break
                    except (IndexError, ValueError):
                        pass
                    break
            break

    # If pactl move didn't work (likely due to EasyEffects), try alternative methods
    if not moved_successfully:
        # Try using pw-cli to move the stream
        # First, find the PipeWire node ID for our target sink
        wpctl_res = subprocess.run(
            ["wpctl", "status"],
            capture_output=True, text=True
        )

        target_node_id = None
        for line in wpctl_res.stdout.split('\n'):
            if sink_name in line:
                try:
                    target_node_id = line.strip().split('.')[0].strip()
                except (IndexError, ValueError):
                    pass
                break

        if target_node_id:
            # Use pw-cli to link the stream to our target
            subprocess.run(
                ["pw-cli", "set-param", app_index, "Props", f"{{ target.object = {target_node_id} }}"],
                check=False, capture_output=True
            )
            time.sleep(0.1)

    return moved_successfully or result.returncode == 0

# -------------------
# VU meter functions
# -------------------
def get_channel_levels():
    """Get audio levels for all channels (for VU meters)"""
    levels = {}
    
    # Get levels from sink-inputs on stream mix and monitor
    res = subprocess.run(["pactl", "list", "sink-inputs"], capture_output=True, text=True)
    output = res.stdout
    
    sections = output.split("Sink Input #")
    for section in sections[1:]:
        lines = section.split('\n')
        if not lines:
            continue
        idx = lines[0].strip().split()[0] if lines[0].strip() else None
        if not idx:
            continue
        
        # Check if this is one of our loopbacks by module ID
        module_id = None
        sink_name = None
        for line in section.split('\n'):
            if 'pulse.module.id = "' in line:
                try:
                    module_id = line.split('pulse.module.id = "')[1].split('"')[0]
                except (IndexError, ValueError):
                    pass
            elif 'target.object = "' in line:
                try:
                    sink_name = line.split('target.object = "')[1].split('"')[0]
                except (IndexError, ValueError):
                    pass
        
        if module_id and sink_name:
            # Find which channel this belongs to
            for ch in CHANNELS:
                stream_mod_id = LOOPBACK_STREAM_MODULE_IDS.get(ch)
                monitor_mod_id = LOOPBACK_MONITOR_MODULE_IDS.get(ch)
                
                if module_id == stream_mod_id:
                    # Get volume level
                    level = _extract_volume_from_section(section)
                    if ch not in levels:
                        levels[ch] = {}
                    levels[ch]['stream'] = level
                elif module_id == monitor_mod_id:
                    level = _extract_volume_from_section(section)
                    if ch not in levels:
                        levels[ch] = {}
                    levels[ch]['monitor'] = level
    
    return levels

def _extract_volume_from_section(section):
    """Extract volume level (0-1) from a sink-input section"""
    for line in section.split('\n'):
        if 'Volume:' in line and 'front-left:' in line:
            try:
                # Volume format: front-left: 65536 / 100% / 0,00 dB
                vol_part = line.split('front-left:')[1].split('/')[1].strip().replace('%', '')
                volume_percent = float(vol_part)
                # Convert to 0-1 range, but also need peak levels
                # For now, use volume as approximation (real VU needs peak detection)
                return min(volume_percent / 100.0, 1.0)
            except (IndexError, ValueError):
                pass
    return 0.0
