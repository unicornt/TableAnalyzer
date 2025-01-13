function mockFetch(url, options) {
    if (url.includes("/api/upload/file")) {
        return {
            code: 1,
            message: "success",
            data: {
                file_url: "https://xxxxx",
            }
        }
    }
    if (url.includes("/v1/chat/completions")) {
        return {
            code: 1,
            message: "success",
            data: {
                content: "This is a test response",
                // 值为空字符串或者生成图片的url
                image_url: "https://xxxxx",
            }
        }
    }
}
function getLLMRes() {
    return mockFetch("https://10.177.46.143:5000/chat", {
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
                            "type": "image || table",
                            "file_url": "https://xxxxxx"
                        }
                    ]
                }
            ],
        },
        method: "POST",
    })
};

function uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);
    return mockFetch("https://10.177.46.143:5000/upload",
        {
            method: "POST",
            body: formData,
        }
    )
}
console.log("llm response:",getLLMRes());
const fileContent = new Blob(['Hello, world!'], { type: 'text/plain' });
const file = new File([fileContent], 'data/student_grades.xlsx', { type: 'text/plain' });
console.log("file url:",uploadFile(file));