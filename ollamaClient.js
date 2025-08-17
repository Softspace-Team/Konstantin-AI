const { request } = require('undici');

exports.sendMessage = async function({
    url,
    model,
    system,
    examples = [],
    userText
}) {
    const payload = {
        model,
        stream: true,
        message: [
            {
                role: 'system', content: system
            },
            ...examples,
            {
                role: 'user', content: userText
            }
        ],
        options: {
            temperature: .4,
            top_p: .85,
            num_ctx: 2048,
            num_predict: 120,
            seed: 42
        }
    };

    const { body } = await request(url, {
        method: 'POST',
        body: JSON.stringify(payload),
        headers: {
            'Content-type': 'application/json'
        }
    });

    let text = '';

    for await (const chunk of body) {
        const lines = chunk.toString('utf8').split('\n').filter(Boolean);

        for (const line of lines) {
            try {
                const j = JSON.parse(line);

                if (j?.message?.content) text += j.message.content;
            }
            catch (err) {

            }
        }
    }

    return text.trim();
}