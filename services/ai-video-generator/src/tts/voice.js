import fs from "fs/promises"
import axios from "axios"
import path from "path"

const OUTPUT_BASE_DIR = process.env.TTS_OUTPUT_DIR ?? "/tmp/zttato-tts"

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
{responseType:"arraybuffer"}
)

const safeOutputPath = resolveOutputPath(output)
await fs.mkdir(path.dirname(safeOutputPath), { recursive: true })
await fs.writeFile(safeOutputPath,response.data)

}
