import axios from "axios";

export async function getRepos(token: string) {
  const res = await axios.get("https://api.github.com/user/repos", {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
    },
  });

  return res.data as Array<{ full_name: string; private: boolean; html_url: string }>;
}
