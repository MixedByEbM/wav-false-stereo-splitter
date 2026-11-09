🎵 WAV False Stereo Splitter

A fast, lightweight utility built for music producers and mixing engineers to instantly clean up DAW audio stems.
When consolidating or exporting audio tracks from modern DAWs, mono signals (like lead vocals, bass, or kick drums) frequently get rendered as two-channel stereo files. These "false stereo" files clutter your session and eat up double the hard drive space.
This software automatically scans WAV files using advanced Cross-Correlation Phase Alignment. It accurately identifies tracks that are essentially mono—even if they have slight timing delays or dither noise from analog modeling plugins—and collapses them down into true, single-channel mono files while preserving the exact original sample rate (44.1k–96k) and bit depth (16/24/32-bit). True stereo files with intentional panning or wide spatial data are safely skipped.

✨ Key Features

• Smart Phase Alignment: Uses cross-correlation metrics to catch vocal stems that sound centered but fail basic subtraction tests due to sub-millisecond phase offsets.
• Preserves Audio Quality: Maintains the exact original sample rate and bit depth properties for a flawless DAW re-import.
• Instant Processing Layout: Displays a live queue of loaded tracks and provides immediate download access or folder export optimization metrics.
• Live Status Log: Groups tracks instantly upon analysis and spits out a clean, grouped summary chart when the batch run finishes.

🛠️ Open Source & Free to Tweak!

This tool was built collaboratively using AI to solve a real-world mixing workflow headache. Because it was born from open-source concepts, it is 100% free and open to everyone.
• For Producers: Enjoy a completely free utility to speed up your session preparation. No hidden fees, no expiration dates, and no data tracking.
• For Coders / Fiddlers: Want to improve the alignment math, change the interface layout, or adapt it entirely for your own custom workflow needs? Please feel free to dive into the source code! Take the Python script, break it apart, modify it, or adapt it for your own needs.
