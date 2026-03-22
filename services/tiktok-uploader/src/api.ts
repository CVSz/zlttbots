import axios from "axios";

type UploadRequest = { title: string; media_url: string; campaign_id: string };

export async function uploadVideo(payload: UploadRequest) {
  const response = await axios.post(process.env.TIKTOK_API as string, {
    title: payload.title,
    video_url: payload.media_url,
  }, {
    headers: { Authorization: `Bearer ${process.env.TIKTOK_TOKEN}` },
  });
  const trackingLink = `${process.env.BASE_URL}/t/${payload.campaign_id}`;
  return { ...response.data, tracking_link: trackingLink };
}
