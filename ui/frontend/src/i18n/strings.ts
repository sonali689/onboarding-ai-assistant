export type Lang = 'en' | 'ja'

export const strings = {
  en: {
    newConversation: 'New conversation',
    recent:          'Recent',
    noChats:         'Your conversations will appear here',
    ready:           'Ready',
    thinking:        'Thinking...',
    tryAsking:       'Try asking',
    subtitle:        "Ask anything about Autoliv's products and processes — in English or Japanese.",
    placeholder:     'Ask in English or Japanese...',
    disclaimer:      'Internal use only · Data stays on Autoliv servers · 社内利用限定',
    fromMaterials:   'From Autoliv training materials',
    generalKnowledge:'General knowledge',
    error:           'Sorry, something went wrong. Please try again.',
    standard:        'Standard',
    extended:        'Extended thinking',
    extendedHint:    'Slower, more thorough',
    localAI:         'Local AI · EN · JA · v2.0',
    suggestions: [
      { text: 'What are inflators and their various types?',    lang: 'EN' },
      { text: 'インフレーターとその種類について教えてください', lang: 'JA' },
    ],
    greetings: {
      earlyMorning: ["Early bird! ",           "Rise and shine "],
      morning:      ["Good morning! ",          "Morning! Let's get started ", "Happy {day}! "],
      afternoon:    ["Good afternoon! ",         "Welcome back ",               "Hey there! "],
      evening:      ["Good evening! ",           "Evening check-in ",           "Almost done for the day? "],
      night:        ["Hello, night owl! ",       "Late night learning ",        "Still at it! "],
    },
  },

  ja: {
    newConversation: '新しい会話',
    recent:          '最近の会話',
    noChats:         '会話履歴がここに表示されます',
    ready:           '準備完了',
    thinking:        '考え中...',
    tryAsking:       '試してみる',
    subtitle:        'Autolivの製品やプロセスについて、日本語または英語で何でも聞いてください。',
    placeholder:     '日本語または英語で質問してください...',
    disclaimer:      '社内利用限定 · データはAutolivサーバーに保存されます',
    fromMaterials:   'Autoliv研修資料より',
    generalKnowledge:'一般知識',
    error:           'エラーが発生しました。もう一度お試しください。',
    standard:        'スタンダード',
    extended:        '詳細分析',
    extendedHint:    'より詳しく、時間がかかります',
    localAI:         'ローカルAI · EN · JA · v2.0',
    suggestions: [
      { text: 'インフレーターとその種類について教えてください', lang: 'JA' },
      { text: 'What are inflators and their various types?',    lang: 'EN' },
    ],
    greetings: {
      earlyMorning: ["早起きですね！",          "おはようございます "],
      morning:      ["おはようございます！",     "今日も頑張りましょう ",      "{day}ですね！"],
      afternoon:    ["こんにちは！",              "お疲れ様です ",               "何かお手伝いできますか？"],
      evening:      ["こんばんは！",              "お疲れ様でした ",             "もうすぐ終わりですね "],
      night:        ["夜遅くまでお疲れ様！",      "夜の学習ですね ",             "まだ頑張ってますね！"],
    },
  },
} as const

export type Strings = typeof strings['en'] | typeof strings['ja']