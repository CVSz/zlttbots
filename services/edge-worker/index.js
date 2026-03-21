export default {
  async fetch(request) {
    const url = new URL(request.url)
    const country = request.headers.get('cf-ipcountry') || 'US'

    let backend = 'https://us.zeaz.dev'
    if (country === 'TH') backend = 'https://asia.zeaz.dev'
    if (country === 'DE') backend = 'https://eu.zeaz.dev'

    const target = new URL(url.pathname + url.search, backend)
    return fetch(new Request(target.toString(), request))
  },
}
