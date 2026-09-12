# iOS note

The current cross-platform desktop target is **macOS**, not iOS/iPadOS.

The iOS idea remains a future separate port because the present Footage Lab engine launches FFmpeg/FFprobe as subprocesses, while an iOS application would need a different in-process media integration and a mobile-native UI. Nothing in the Windows/macOS desktop release depends on this deferred port.
