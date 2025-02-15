import requests
resp = requests.post('https://textbelt.com/text', {
  'phone': '2032465757',
  'message': 'Hello world',
  'key': '8f81fa4776d152bda7296b7d91370e0a6a88a7fb37dXKZouUBVXyozsQuYOj9ulJ',
})
print(resp.json())