import dotenv from "dotenv"

dotenv.config()

7export const config = {
db: process.env.DB_URL,
videoDir: process.env.VIDEO_DIR || "./videos",
}
