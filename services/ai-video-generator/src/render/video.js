import ffmpeg from "fluent-ffmpeg"

export function renderVideo(image, voice, subtitle, output){

return new Promise((resolve,reject)=>{

ffmpeg()

.input(image)
.loop(10)

.input(voice)

.videoFilters([
{
filter:"subtitles",
options:subtitle
}
])

.outputOptions([
"-c:v libx264",
"-c:a aac",
"-shortest",
"-pix_fmt yuv420p"
])

.save(output)

.on("end",resolve)
.on("error",reject)

})

}
