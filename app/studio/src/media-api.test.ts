import { afterEach, describe, expect, it, vi } from "vitest";
import { generateImage, getModelsStatus, synthesizeSpeech, transcribeAudio } from "./api";

const realFetch = global.fetch;
afterEach(() => {
  global.fetch = realFetch;
  vi.restoreAllMocks();
});

function stubFetch(res: Partial<Response>): ReturnType<typeof vi.fn> {
  const fn = vi.fn().mockResolvedValue(res);
  global.fetch = fn as unknown as typeof fetch;
  return fn;
}

describe("generateImage", () => {
  it("POSTs the prompt + options and returns the result", async () => {
    const fn = stubFetch({
      ok: true,
      status: 200,
      json: async () => ({ url: "/media/images/a.png", prompt: "p", seed: 7, seconds: 1.2 }),
    });
    const result = await generateImage("p", { steps: 4, seed: 7 });
    expect(result.url).toBe("/media/images/a.png");
    const [path, init] = fn.mock.calls[0] as [string, RequestInit];
    expect(path).toBe("/api/image");
    expect(JSON.parse(init.body as string)).toMatchObject({ prompt: "p", steps: 4, seed: 7 });
  });

  it("surfaces the server's JSON error message (e.g. a 501 install hint)", async () => {
    stubFetch({
      ok: false,
      status: 501,
      json: async () => ({ error: "image generation needs mflux — pip install 'agency-studio[media]'" }),
    });
    await expect(generateImage("p")).rejects.toThrow(/mflux/);
  });
});

describe("synthesizeSpeech", () => {
  it("omits voice when not given, includes it when given", async () => {
    const fn = stubFetch({ ok: true, status: 200, json: async () => ({ url: "/media/audio/a.wav", voice: "af_heart", seconds: 0.4 }) });
    await synthesizeSpeech("hello");
    expect(JSON.parse((fn.mock.calls[0][1] as RequestInit).body as string)).toEqual({ text: "hello" });
    await synthesizeSpeech("hello", "af_sky");
    expect(JSON.parse((fn.mock.calls[1][1] as RequestInit).body as string)).toEqual({ text: "hello", voice: "af_sky" });
  });
});

describe("transcribeAudio", () => {
  it("sends the blob bytes with its MIME type and returns the transcript", async () => {
    const fn = stubFetch({ ok: true, status: 200, json: async () => ({ text: "hello world", seconds: 0.9 }) });
    const blob = new Blob([new Uint8Array([1, 2, 3])], { type: "audio/wav" });
    const result = await transcribeAudio(blob);
    expect(result.text).toBe("hello world");
    const init = fn.mock.calls[0][1] as RequestInit;
    expect((init.headers as Record<string, string>)["Content-Type"]).toBe("audio/wav");
    expect(init.body).toBe(blob);
  });

  it("defaults Content-Type to audio/wav for a typeless blob", async () => {
    const fn = stubFetch({ ok: true, status: 200, json: async () => ({ text: "", seconds: 0.1 }) });
    await transcribeAudio(new Blob([new Uint8Array([0])]));
    const init = fn.mock.calls[0][1] as RequestInit;
    expect((init.headers as Record<string, string>)["Content-Type"]).toBe("audio/wav");
  });
});

describe("getModelsStatus", () => {
  it("returns the resident model + ids", async () => {
    stubFetch({ ok: true, status: 200, json: async () => ({ resident: "image", models: { image: "schnell" } }) });
    const status = await getModelsStatus();
    expect(status.resident).toBe("image");
    expect(status.models.image).toBe("schnell");
  });
});
