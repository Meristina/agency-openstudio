"""engines — local inference back-ends for Agency Studio.

Wave 2 adds ``local_media`` (image / speech-to-text / text-to-speech on Apple
Silicon via MLX). Everything here is optional: the modules import their heavy
back-ends lazily, so the core stdlib server runs with the ``[media]`` extra absent.
"""
