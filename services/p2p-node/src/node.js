import { createLibp2p } from 'libp2p'
import { tcp } from '@libp2p/tcp'
import { noise } from '@chainsafe/libp2p-noise'
import { mplex } from '@libp2p/mplex'
import process from 'node:process'

const ALLOWLIST = (process.env.PEER_ALLOWLIST || '').split(',').map((peer) => peer.trim()).filter(Boolean)

export async function startNode() {
  const node = await createLibp2p({
    transports: [tcp()],
    connectionEncryption: [noise()],
    streamMuxers: [mplex()]
  })

  node.addEventListener('peer:connect', async (evt) => {
    const peerId = evt.detail.toString()
    if (ALLOWLIST.length > 0 && !ALLOWLIST.includes(peerId)) {
      await node.hangUp(evt.detail)
    }
  })

  await node.start()
  return node
}

if (process.env.NODE_ENV !== 'test') {
  startNode().then(() => {
    console.log('p2p node started with allowlist size', ALLOWLIST.length)
  }).catch((error) => {
    console.error('failed to start p2p node', error)
    process.exitCode = 1
  })
}
