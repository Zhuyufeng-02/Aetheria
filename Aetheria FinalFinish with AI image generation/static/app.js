 // 初始化变量
let selectedCrystal = null;
let currentCards = [];

// DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded - initializing app...');
    initializeCrystals();
    bindEvents();

    // 调试信息
    const promptInput = document.getElementById('promptInput');
    const generateBtn = document.getElementById('generateBtn');
    console.log('promptInput element:', promptInput);
    console.log('generateBtn element:', generateBtn);
});

// 初始化水晶选择
function initializeCrystals() {
    const crystalList = document.getElementById('crystalList');
    if (!crystalList) {
        console.error('crystalList element not found!');
        return;
    }

    const crystals = [
        { name: 'amethyst', color: '#9966CC', emoji: '🔮' },
        { name: 'quartz', color: '#F0F8FF', emoji: '💎' },
        { name: 'emerald', color: '#50C878', emoji: '💚' },
        { name: 'ruby', color: '#E0115F', emoji: '❤️' },
        { name: 'sapphire', color: '#0F52BA', emoji: '💙' },
        { name: 'citrine', color: '#E4D00A', emoji: '💛' }
    ];

    crystalList.innerHTML = crystals.map(crystal => `
        <div class="crystal-item" data-crystal="${crystal.name}" style="background: ${crystal.color}; padding: 1rem; border-radius: 15px; text-align: center; cursor: pointer; transition: all 0.3s ease; border: 2px solid transparent; color: white; font-weight: bold;">
            <div class="crystal-emoji" style="font-size: 2rem; margin-bottom: 0.5rem;">${crystal.emoji}</div>
            <div class="crystal-name" style="text-transform: capitalize; font-size: 0.9rem;">${crystal.name}</div>
        </div>
    `).join('');

    // 绑定水晶点击事件
    document.querySelectorAll('.crystal-item').forEach(item => {
        item.addEventListener('click', function() {
            selectCrystal(this.dataset.crystal, this);
        });
    });

    console.log('Crystals initialized');
}

// 绑定事件
function bindEvents() {
    const drawBtn = document.getElementById('drawBtn');
    const generateBtn = document.getElementById('generateBtn');
    const chatForm = document.getElementById('chatForm');
    const ctaGenerate = document.getElementById('ctaGenerate');

    console.log('Binding events...');
    console.log('drawBtn:', drawBtn);
    console.log('generateBtn:', generateBtn);
    console.log('chatForm:', chatForm);
    console.log('ctaGenerate:', ctaGenerate);

    if (drawBtn) {
        drawBtn.addEventListener('click', drawCards);
        console.log('Bound drawCards to drawBtn');
    }
    if (generateBtn) {
        generateBtn.addEventListener('click', generateImage);
        console.log('Bound generateImage to generateBtn');
    }
    if (chatForm) {
        chatForm.addEventListener('submit', sendChatMessage);
        console.log('Bound sendChatMessage to chatForm');
    }
    if (ctaGenerate) {
        ctaGenerate.addEventListener('click', quickGenerate);
        console.log('Bound quickGenerate to ctaGenerate');
    }
}

// 选择水晶
function selectCrystal(crystalName, element) {
    selectedCrystal = crystalName;

    // 移除其他水晶的选中状态
    document.querySelectorAll('.crystal-item').forEach(item => {
        item.classList.remove('selected');
        item.style.border = '2px solid transparent';
    });

    // 添加当前水晶的选中状态
    element.classList.add('selected');
    element.style.border = '2px solid gold';
    element.style.boxShadow = '0 0 20px gold';

    // 水晶球效果
    const crystalBall = document.getElementById('crystalBall');
    if (crystalBall) {
        crystalBall.style.animation = 'pulse 1s ease-in-out';
        setTimeout(() => {
            crystalBall.style.animation = '';
        }, 1000);
    }

    console.log('Selected crystal:', crystalName);
}

// 抽取卡片
async function drawCards() {
    console.log('drawCards called');
    if (!selectedCrystal) {
        alert('Please select a crystal first!');
        return;
    }

    const readingSelect = document.getElementById('readingSelect');
    const readingType = readingSelect ? readingSelect.value : 'single';
    const cardsContainer = document.getElementById('readingResult');

    if (!cardsContainer) {
        console.error('cardsContainer not found');
        return;
    }

    // 显示加载状态
    cardsContainer.innerHTML = '<div class="loading">Drawing cards...</div>';

    try {
        const response = await fetch('/api/cards', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                reading: readingType,
                crystal: selectedCrystal
            })
        });

        const data = await response.json();

        if (data.cards && data.cards.length > 0) {
            currentCards = data.cards;
            displayCards(data.cards);
            addChatMessage(data.message, 'bot');
        } else {
            throw new Error('No cards received');
        }
    } catch (error) {
        console.error('Error drawing cards:', error);
        cardsContainer.innerHTML = '<div class="error">Failed to draw cards. Please try again.</div>';
    }
}

// 显示卡片
function displayCards(cards) {
    const cardsContainer = document.getElementById('readingResult');
    if (!cardsContainer) return;

    cardsContainer.innerHTML = cards.map((card, index) => `
        <div class="card" data-index="${index}" style="perspective: 1000px; height: 300px; margin: 1rem;">
            <div class="card-inner ${card.reversed ? 'reversed' : ''}" style="position: relative; width: 100%; height: 100%; transition: transform 0.6s; transform-style: preserve-3d; cursor: pointer;">
                <div class="card-front" style="position: absolute; width: 100%; height: 100%; backface-visibility: hidden; border-radius: 15px; padding: 1rem; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: 2px solid gold;">
                    <h3>${card.name}</h3>
                    <p>${card.meaning}</p>
                    ${card.reversed ? '<div class="reversal-note" style="font-style: italic; margin-top: 0.5rem; color: #ff6b6b;">(Reversed)</div>' : ''}
                </div>
                <div class="card-back" style="position: absolute; width: 100%; height: 100%; backface-visibility: hidden; border-radius: 15px; padding: 1rem; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; transform: rotateY(180deg);">
                    <div class="card-symbol" style="font-size: 3rem;">✨</div>
                </div>
            </div>
            <button class="generate-from-card" onclick="generateFromCard(${index})" style="margin-top: 1rem; padding: 0.5rem 1rem; background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); border-radius: 20px; color: white; cursor: pointer; transition: all 0.3s ease; width: 100%;">
                Generate Image for this Card
            </button>
        </div>
    `).join('');

    // 添加卡片翻转动画
    setTimeout(() => {
        document.querySelectorAll('.card').forEach((card, index) => {
            card.style.animationDelay = `${index * 0.2}s`;
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.animation = 'cardAppear 0.5s ease-out forwards';
        });
    }, 100);

    // 添加悬停翻转效果
    document.querySelectorAll('.card-inner').forEach(inner => {
        inner.addEventListener('mouseenter', function() {
            this.style.transform = 'rotateY(180deg)';
        });
        inner.addEventListener('mouseleave', function() {
            this.style.transform = 'rotateY(0deg)';
        });
    });
}

// 从卡片生成图像
async function generateFromCard(cardIndex) {
    console.log('generateFromCard called for card index:', cardIndex);
    const card = currentCards[cardIndex];
    if (!card) return;

    const promptInput = document.getElementById('promptInput');
    if (promptInput) {
        promptInput.value = `Tarot card: ${card.name} - ${card.meaning}`;
        console.log('Set prompt from card:', promptInput.value);
    }

    await generateImage();
}

// 生成图像
async function generateImage() {
    console.log('generateImage called');

    const promptInput = document.getElementById('promptInput');
    const preview = document.getElementById('generatedPreview');

    if (!promptInput) {
        console.error('promptInput not found!');
        alert('Prompt input not found!');
        return;
    }
    if (!preview) {
        console.error('generatedPreview not found!');
        alert('Preview area not found!');
        return;
    }

    const prompt = promptInput.value.trim();
    console.log('Prompt value:', prompt);

    if (!prompt) {
        alert('Please enter a prompt for image generation');
        return;
    }

    // 显示加载状态
    preview.innerHTML = `
        <div style="text-align: center; padding: 20px; color: white;">
            <div style="border: 3px solid rgba(255,255,255,0.3); border-radius: 50%; border-top: 3px solid white; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 10px;"></div>
            <p>Generating mystical image with AI...</p>
            <p style="font-size: 14px; opacity: 0.7;">This may take a few seconds</p>
        </div>
        <style>
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    `;

    try {
        console.log('Sending request to /api/generate...');

        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: prompt,
                crystal: selectedCrystal || 'unknown',
                width: 512,
                height: 768
            })
        });

        const data = await response.json();
        console.log('Response received:', data);

        if (data.success && data.image) {
            preview.innerHTML = `
                <div style="text-align: center; background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px;">
                    <h4 style="color: gold; margin-bottom: 15px;">✨ Generated Mystical Image ✨</h4>
                    <div style="margin: 15px 0;">
                        <img src="${data.image}" alt="Generated image" style="max-width: 100%; max-height: 400px; border-radius: 10px; border: 2px solid gold;">
                    </div>
                    <div style="text-align: left; background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; margin-top: 15px;">
                        <p><strong>Prompt:</strong> ${data.prompt}</p>
                        <p><strong>Crystal:</strong> ${selectedCrystal || 'None'}</p>
                        ${data.note ? `<p><em>${data.note}</em></p>` : ''}
                        <button onclick="saveImage('${data.image.replace(/'/g, "\\'")}', '${prompt.replace(/'/g, "\\'")}')" style="background: #2196F3; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-top: 10px;">
                            Save to Gallery
                        </button>
                    </div>
                </div>
            `;

            // 添加到聊天记录
            addChatMessage(`I've generated a mystical image for: "${prompt}"`, 'bot');
        } else {
            preview.innerHTML = `
                <div style="background: rgba(255,0,0,0.1); border: 1px solid rgba(255,0,0,0.3); padding: 15px; border-radius: 8px; color: #ff6b6b;">
                    <h4>Generation Failed</h4>
                    <p>${data.note || 'Unknown error occurred'}</p>
                    <button onclick="generateImage()" style="background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); color: white; padding: 8px 16px; border-radius: 5px; cursor: pointer; margin-top: 10px;">
                        Try Again
                    </button>
                </div>
            `;
        }
    } catch (error) {
        console.error('Generation failed:', error);
        preview.innerHTML = `
            <div style="background: rgba(255,0,0,0.1); border: 1px solid rgba(255,0,0,0.3); padding: 15px; border-radius: 8px; color: #ff6b6b;">
                <h4>Generation Failed</h4>
                <p>Network error: ${error.message}</p>
                <p>Please check the browser console for details.</p>
                <button onclick="generateImage()" style="background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); color: white; padding: 8px 16px; border-radius: 5px; cursor: pointer; margin-top: 10px;">
                    Try Again
                </button>
            </div>
        `;
    }
}

// 快速生成（CTA按钮）
async function quickGenerate() {
    console.log('quickGenerate called');
    const prompts = [
        "A mystical crystal ball showing the future",
        "Tarot card with magical symbols and stars",
        "Mystical forest with glowing crystals",
        "Celestial constellation in deep space",
        "Ancient runes with magical energy"
    ];

    const promptInput = document.getElementById('promptInput');
    if (promptInput) {
        promptInput.value = prompts[Math.floor(Math.random() * prompts.length)];
        console.log('Set random prompt:', promptInput.value);
    }

    // 如果没有选择水晶，随机选择一个
    if (!selectedCrystal) {
        const crystals = document.querySelectorAll('.crystal-item');
        if (crystals.length > 0) {
            const randomCrystal = crystals[Math.floor(Math.random() * crystals.length)];
            selectCrystal(randomCrystal.dataset.crystal, randomCrystal);
            console.log('Auto-selected crystal:', randomCrystal.dataset.crystal);
        }
    }

    await generateImage();
}

// 保存图像（模拟功能）
function saveImage(imageData, prompt) {
    // 在实际应用中，这里会调用后端API保存图像
    alert('Image saved to gallery! (This is a demo - in a real app, this would save to your gallery)');
    addChatMessage('Your generated image has been saved to the gallery!', 'bot');
}

// 聊天功能
async function sendChatMessage(event) {
    event.preventDefault();

    const chatInput = document.getElementById('chatInput');
    const chatLog = document.getElementById('chatLog');

    if (!chatInput || !chatLog) return;

    const message = chatInput.value.trim();
    if (!message) return;

    // 添加用户消息
    addChatMessage(message, 'user');
    chatInput.value = '';

    // 显示输入指示器
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.style.display = 'block';
    }

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                crystal: selectedCrystal
            })
        });

        const data = await response.json();

        // 隐藏输入指示器
        if (typingIndicator) {
            typingIndicator.style.display = 'none';
        }

        // 添加机器人回复
        addChatMessage(data.reply, 'bot');

    } catch (error) {
        console.error('Chat error:', error);
        if (typingIndicator) {
            typingIndicator.style.display = 'none';
        }
        addChatMessage('I apologize, but I cannot respond at the moment.', 'bot');
    }
}

// 添加聊天消息
function addChatMessage(message, sender) {
    const chatLog = document.getElementById('chatLog');
    if (!chatLog) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}-message`;
    messageDiv.style.marginBottom = '1rem';
    messageDiv.style.display = 'flex';
    messageDiv.style.justifyContent = sender === 'user' ? 'flex-end' : 'flex-start';

    messageDiv.innerHTML = `
        <div class="message-bubble" style="max-width: 70%; padding: 0.75rem 1rem; border-radius: 18px; word-wrap: break-word; background: ${sender === 'user' ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : 'rgba(255,255,255,0.1)'}; color: white; border: ${sender === 'bot' ? '1px solid rgba(255,255,255,0.2)' : 'none'};">
            ${message}
        </div>
    `;

    chatLog.appendChild(messageDiv);
    chatLog.scrollTop = chatLog.scrollHeight;
}

// 处理键盘事件
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        const activeElement = document.activeElement;
        if (activeElement.id === 'chatInput') {
            event.preventDefault();
            sendChatMessage(event);
        }
    }
}

// 绑定键盘事件
document.addEventListener('keypress', handleKeyPress);

// 添加卡片出现动画
const style = document.createElement('style');
style.textContent = `
    @keyframes cardAppear {
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
`;
document.head.appendChild(style);