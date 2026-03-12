import { generateVoice } from "../tts/voice.js"
import { generateSubtitle } from "../subtitle/subtitle.js"
import { renderVideo } from "../render/video.js"

export async function generateVideo(product){

const voiceFile = `voice_${product.id}.mp3`
const subtitleFile = `sub_${product.id}.srt`
const videoFile = `video_${product.id}.mp4`

const script = product.script

await generateVoice(script, voiceFile)

generateSubtitle(script, subtitleFile)

await renderVideo(
product.image,
voiceFile,
subtitleFile,
videoFile
)

return videoFile

}
