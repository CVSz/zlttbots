import fs from "fs"
import axios from "axios"

export async function generateVoice(text, output){

const url = "https://api.elevenlabs.io/v1/text-to-speech"

const response = await axios.post(
url,
{text},
{responseType:"arraybuffer"}
)

fs.writeFileSync(output,response.data)

}
