import fs from "fs/promises"
import axios from "axios"
import path from "path"
import { constants as fsConstants } from "fs"

const OUTPUT_BASE_DIR = process.env.TTS_OUTPUT_DIR ?? "/tmp/zttato-tts"
const MAX_AUDIO_BYTES = Number.parseInt(process.env.TTS_MAX_AUDIO_BYTES ?? "5242880", 10)

function resolveOutputPath(output) {
  const normalized = path.resolve(OUTPUT_BASE_DIR, output)
  const baseDir = path.resolve(OUTPUT_BASE_DIR)
  if (!normalized.startsWith(`${baseDir}${path.sep}`) && normalized !== baseDir) {
    throw new Error("Output path is outside allowed TTS directory")
  }
  return normalized
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
if (!response.data || response.data.byteLength > MAX_AUDIO_BYTES) {
  throw new Error("TTS audio response exceeds configured size limit")
}

const safeOutputPath = resolveOutputPath(output)
await fs.mkdir(path.dirname(safeOutputPath), { recursive: true })
await fs.writeFile(safeOutputPath,response.data,{ mode: 0o600, flag: fsConstants.O_CREAT | fsConstants.O_EXCL | fsConstants.O_WRONLY })

}
