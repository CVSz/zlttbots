import axios from "axios";

export async function uploadVideo(payload: { title: string; media_url: string }) {
  const response = await axios.post(process.env.TIKTOK_API as string, payload, {
    headers: { Authorization: `Bearer ${process.env.TIKTOK_TOKEN}` },
  });
  return response.data;
}
