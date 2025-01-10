fetch("https://api.openai.com/v1/chat/completions", {
    body: {
        model: "gpt-4o",
        temperature: 0.8,
        top_p: 0.9,
        frequency_penalty: 0,
        presence_penalty: 0,
        max_tokens: 3000,
        n: 1,
        stream: true,
        messages: [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What is in this image?"
                    },
                    {
                        "type": "file",
                        "file_url": "https://xxxxxx"
                    }
                ]
            }
        ],
    },
    method: "POST",
});

fetch("https://bzxxx/api/upload/file",
    {
        method: "POST",
        body: formData,
    }
)
response = {
    code: 1,
    message: "success",
    data: {
        file_url: "https://xxxxx",
    }
}
