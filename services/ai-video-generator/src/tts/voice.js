import fs from "fs/promises"
import axios from "axios"
import path from "path"
import { constants as fsConstants } from "fs"

const OUTPUT_BASE_DIR = process.env.TTS_OUTPUT_DIR ?? "/tmp/zttato-tts"
const MAX_AUDIO_BYTES = Number.parseInt(process.env.TTS_MAX_AUDIO_BYTES ?? "5242880", 10)
const SAFE_FILENAME_PATTERN = /^[A-Za-z0-9._-]+$/

function validateFilename(output) {
  if (typeof output !== "string" || output.length === 0) {
    throw new Error("Audio output filename is required")
  }
  if (!SAFE_FILENAME_PATTERN.test(output)) {
    throw new Error("Audio output filename contains disallowed characters")
  }
  if (path.basename(output) !== output) {
    throw new Error("Audio output filename must not include path segments")
  }
}

function resolveOutputPath(output) {
  validateFilename(output)
  const normalized = path.resolve(OUTPUT_BASE_DIR, output)
  const baseDir = path.resolve(OUTPUT_BASE_DIR)
  if (!normalized.startsWith(`${baseDir}${path.sep}`) && normalized !== baseDir) {
    throw new Error("Output path is outside allowed TTS directory")
  }
  return normalized
}

function hasKnownAudioHeader(buffer) {
  const bytes = new Uint8Array(buffer)
  if (bytes.length < 4) {
    return false
  }
  const isWav = bytes[0] === 0x52 && bytes[1] === 0x49 && bytes[2] === 0x46 && bytes[3] === 0x46
  const isMp3 = bytes[0] === 0x49 && bytes[1] === 0x44 && bytes[2] === 0x33
  const isOgg = bytes[0] === 0x4f && bytes[1] === 0x67 && bytes[2] === 0x67 && bytes[3] === 0x53
  return isWav || isMp3 || isOgg
}

function toSafeAudioBuffer(payload) {
  const audioBuffer = Buffer.isBuffer(payload) ? payload : Buffer.from(payload)
  if (audioBuffer.length === 0 || audioBuffer.length > MAX_AUDIO_BYTES) {
    throw new Error("TTS audio response exceeds configured size limit")
  }
  if (!hasKnownAudioHeader(audioBuffer)) {
    throw new Error("Unexpected audio binary payload returned by TTS provider")
  }
  return audioBuffer
}

export async function generateVoice(text, output){

const url = "https://api.elevenlabs.io/v1/text-to-speech"

const response = await axios.post(
url,
{text},
{responseType:"arraybuffer", maxContentLength: MAX_AUDIO_BYTES, timeout: 15000}
)

const contentType = String(response.headers["content-type"] ?? "")
if (!contentType.startsWith("audio/")) {
  throw new Error("Unexpected content type returned by TTS provider")
}
const safeAudioBuffer = toSafeAudioBuffer(response.data)

const safeOutputPath = resolveOutputPath(output)
await fs.mkdir(path.dirname(safeOutputPath), { recursive: true })
await fs.writeFile(safeOutputPath,safeAudioBuffer,{ mode: 0o600, flag: fsConstants.O_CREAT | fsConstants.O_EXCL | fsConstants.O_WRONLY })

}
