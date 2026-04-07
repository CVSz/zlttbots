export function generatePublicUrl(projectId: string) {
  const rootDomain = process.env.PUBLIC_DEPLOY_ROOT_DOMAIN ?? "zlttbots.dev";
  return `https://${projectId}.${rootDomain}`;
}
