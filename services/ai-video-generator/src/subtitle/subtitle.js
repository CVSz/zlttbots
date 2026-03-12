import fs from "fs"

export function generateSubtitle(text, output){

const lines = text.split(". ")

let srt = ""

lines.forEach((l,i)=>{

srt += `${i+1}\n`
srt += `00:00:${String(i*3).padStart(2,"0")},000 --> 00:00:${String((i+1)*3).padStart(2,"0")},000\n`
srt += l + "\n\n"

})

fs.writeFileSync(output,srt)

}
