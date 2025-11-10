const crystals = [
  { id: 'rose', name: 'Rose Quartz', color: '#f7c6d3' },
  { id: 'amethyst', name: 'Amethyst', color: '#c9a9ff' },
  { id: 'citrine', name: 'Citrine', color: '#ffe29a' },
  { id: 'clear', name: 'Clear Quartz', color: '#e6f7ff' },
]

let selectedCrystal = null
let audioCtx = null

function playChime(){
  try{
    if(!audioCtx) audioCtx = new (window.AudioContext||window.webkitAudioContext)()
    const o = audioCtx.createOscillator()
    const g = audioCtx.createGain()
    o.type = 'sine'
    o.frequency.setValueAtTime(440, audioCtx.currentTime)
    g.gain.setValueAtTime(0, audioCtx.currentTime)
    g.gain.linearRampToValueAtTime(0.12, audioCtx.currentTime + 0.02)
    g.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 1.4)
    o.connect(g); g.connect(audioCtx.destination);
    o.start(); o.stop(audioCtx.currentTime + 1.5)
  }catch(e){console.warn('audio failed',e)}
}

function renderCrystals() {
  const list = document.getElementById('crystalList')
  crystals.forEach(c => {
    const el = document.createElement('button')
    el.className = 'crystal pulse'
    el.setAttribute('aria-pressed', 'false')
    el.innerHTML = `<svg><use href="/static/images/crystals.svg#crystal-${c.id}"></use></svg><span class="label">${c.name}</span>`
    el.onclick = () => {
      selectedCrystal = c.id
      document.querySelectorAll('.crystal').forEach(x => x.classList.remove('selected'))
      el.classList.add('selected')
      el.setAttribute('aria-pressed', 'true')
    }
    list.appendChild(el)
  })
}

async function drawReading() {
  const reading = document.getElementById('readingSelect').value
  const res = await fetch('/api/cards', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ reading, crystal: selectedCrystal })
  })
  const data = await res.json()
  const out = document.getElementById('readingResult')
  out.innerHTML = ''
  // create flippable card elements
  data.cards.forEach((c, i) => {
    const card = document.createElement('div')
    card.className = 'card'

    const inner = document.createElement('div')
    inner.className = 'inner'

    const back = document.createElement('div')
    back.className = 'face back'
    const img = document.createElement('img')
    img.src = '/static/images/card-back.svg'
    back.appendChild(img)

    const front = document.createElement('div')
    front.className = 'face front'
    if (c.image) {
      const imgFront = document.createElement('img')
      imgFront.src = c.image
      imgFront.alt = c.name
      imgFront.style.width = '100%'
      imgFront.style.height = '100%'
      imgFront.style.objectFit = 'cover'
      // overlay meaning
      const overlay = document.createElement('div')
      overlay.style.position = 'absolute'
      overlay.style.left = '0'
      overlay.style.right = '0'
      overlay.style.bottom = '0'
      overlay.style.padding = '10px'
      overlay.style.background = 'linear-gradient(transparent, rgba(255,255,255,0.95))'
      overlay.innerHTML = `<h3 style="margin:0;font-size:14px">${c.name}${c.reversed? ' (reversed)':''}</h3><p style="margin:6px 0 0;font-size:12px;color:#333">${c.meaning}</p>`
      front.appendChild(imgFront)
      front.appendChild(overlay)
    } else {
      front.innerHTML = `<h3>${c.name}${c.reversed? ' (reversed)':''}</h3><p>${c.meaning}</p>`
    }

    inner.appendChild(back)
    inner.appendChild(front)
    card.appendChild(inner)
    out.appendChild(card)

    // stagger flipping for nicer effect
    setTimeout(() => {
      card.classList.add('flipped')
    }, 350 * i)
  })
}

function appendChat(role, text) {
  const log = document.getElementById('chatLog')
  const el = document.createElement('div')
  el.className = 'chat-item ' + role
  el.textContent = text
  log.appendChild(el)
  log.scrollTop = log.scrollHeight
}

async function sendChat(message) {
  appendChat('user', message)
  const typing = document.getElementById('typingIndicator')
  typing.style.display = 'block'
  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ message, crystal: selectedCrystal })
    })
    const data = await res.json()
    // small delay to simulate composition
    await new Promise(r => setTimeout(r, 350))
    appendChat('bot', data.reply)
  } catch (err) {
    appendChat('bot', 'The fortune teller is momentarily unavailable.')
  } finally {
    typing.style.display = 'none'
  }
}

document.addEventListener('DOMContentLoaded', () => {
  renderCrystals()
  document.getElementById('drawBtn').addEventListener('click', drawReading)
  document.getElementById('generateBtn').addEventListener('click', async () => {
    const prompt = document.getElementById('promptInput').value
    const btn = document.getElementById('generateBtn')
    btn.disabled = true
    btn.textContent = 'Generating...'
    playChime()
    try{
      const res = await fetch('/api/generate', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt,crystal:selectedCrystal})})
      const data = await res.json()
      const prev = document.getElementById('generatedPreview')
      prev.innerHTML = ''
      const img = document.createElement('img')
      img.src = data.image
      img.alt = 'Generated card'
      prev.appendChild(img)
      // allow user to click generated image to interpret/chat
      img.addEventListener('click', ()=>{
        appendChat('system','You selected the generated card for interpretation.')
        sendChat('Interpret this card: ' + (data.prompt||'visual')).then(()=>{})
      })
    }catch(e){
      appendChat('system','Generation failed. Using a placeholder.')
    }finally{
      btn.disabled = false
      btn.textContent = 'Generate Card Image'
    }
  })

  const form = document.getElementById('chatForm')
  form.addEventListener('submit', (e) => {
    e.preventDefault()
    const input = document.getElementById('chatInput')
    const text = input.value.trim()
    if (!text) return
    input.value = ''
    sendChat(text)
  })
})
