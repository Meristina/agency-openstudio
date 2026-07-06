import type { CapabilityEntry, CapabilityInventory, Family } from "../../types";

function entry(family: Family, id: string, label: string, extra: Partial<CapabilityEntry> = {}): CapabilityEntry {
  return {
    id,
    label,
    family,
    cost: "free",
    availability: "available",
    reason: null,
    enablement: null,
    tier: "LOCAL",
    note: "",
    default: false,
    key_env: null,
    ...extra,
  };
}

export function sampleInventory(): CapabilityInventory {
  return {
    generated_at: "now",
    families: [
      {
        family: "image",
        selectable: true,
        selected: null,
        selected_stale: false,
        env_override: null,
        active: "image-local",
        entries: [
          entry("image", "image-local", "Local Image", { default: true, availability: "unavailable", reason: "missing_model_files" }),
          entry("image", "image-cloud", "Cloud Image", { cost: "paid", availability: "unavailable", reason: "API key not set", key_env: "AGENCY_IMAGE_KEY" }),
        ],
      },
      {
        family: "video",
        selectable: true,
        selected: null,
        selected_stale: false,
        env_override: null,
        active: "video-local",
        entries: [
          entry("video", "video-local", "Local Video", { default: true }),
          entry("video", "video-studio", "Studio Video"),
          entry("video", "video-cloud", "Cloud Video", { cost: "paid", availability: "unavailable", reason: "API key not set", key_env: "AGENCY_VIDEO_KEY" }),
        ],
      },
      {
        family: "visual",
        selectable: true,
        selected: "old-vision",
        selected_stale: true,
        env_override: "AGENCY_VISUAL_MODEL",
        active: "visual-local",
        entries: [entry("visual", "visual-local", "Local Vision", { default: true })],
      },
      { family: "embedding", selectable: true, selected: null, selected_stale: false, env_override: null, active: "embed", entries: [entry("embedding", "embed", "Local Search", { default: true })] },
      { family: "kg-extraction", selectable: true, selected: null, selected_stale: false, env_override: null, active: "kg", entries: [entry("kg-extraction", "kg", "Local Knowledge", { default: true })] },
      { family: "stt", selectable: true, selected: null, selected_stale: false, env_override: null, active: "stt", entries: [entry("stt", "stt", "Local Transcription", { default: true })] },
      { family: "tts", selectable: true, selected: null, selected_stale: false, env_override: null, active: "tts", entries: [entry("tts", "tts", "Local Voice", { default: true })] },
      { family: "production-tools", selectable: false, selected: null, selected_stale: false, env_override: null, active: "tools", entries: [entry("production-tools", "tools", "Local Tools", { default: true })] },
      { family: "mcp", selectable: false, selected: null, selected_stale: false, env_override: null, active: "mcp", entries: [entry("mcp", "mcp", "Connectors", { default: true })] },
    ],
  };
}
