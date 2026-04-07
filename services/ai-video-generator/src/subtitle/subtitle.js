import fs from "fs"
import path from "path"

const SUBTITLE_OUTPUT_DIR = process.env.SUBTITLE_OUTPUT_DIR ?? process.cwd()
const SAFE_FILENAME_PATTERN = /^[A-Za-z0-9._-]+$/

function safeSubtitlePath(output) {
  if (!SAFE_FILENAME_PATTERN.test(output)) {
    throw new Error("Invalid subtitle filename")
  }

  const baseDir = path.resolve(SUBTITLE_OUTPUT_DIR)
  const resolvedPath = path.resolve(baseDir, output)
  if (!resolvedPath.startsWith(`${baseDir}${path.sep}`) && resolvedPath !== baseDir) {
    throw new Error("Subtitle output path is outside the allowed directory")
  }

  return resolvedPath
}

export function generateSubtitle(text, output){

const lines = text.split(". ")

let srt = ""

lines.forEach((l,i)=>{

srt += `${i+1}\n`
srt += `00:00:${String(i*3).padStart(2,"0")},000 --> 00:00:${String((i+1)*3).padStart(2,"0")},000\n`
srt += l + "\n\n"

})

const subtitlePath = safeSubtitlePath(output)
fs.mkdirSync(path.dirname(subtitlePath), { recursive: true })
fs.writeFileSync(subtitlePath,srt,{ flag: "wx", mode: 0o600 })

}
