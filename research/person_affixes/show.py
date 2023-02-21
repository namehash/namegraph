import json

s = json.load(open('s.json'))

affixes = ['0x', '_', 'the', '$', 'crypto', 'iam', 'dr', '-', 'meta', 'mr', 'not', 'im', 'nft', 'real', 'eth', 'king',
           'its', 'web', 'web3', 'miss', 'queen', 'ilove', '💎', 'i❤', 'mrs', 'official', '👑', '__', '🏳‍🌈', '•', '❤',
           '🇪🇺', '😎', '₿', 'mr-', '🏴‍☠', 'nft', 'vault', 'wallet', 'crypto', '0', '69', '®', '22', '888', '❤', '100',
           '$', '666', '👑', '1⃣', '🔥', '💎', '💸', '✨', '🌈', '🧡', '😍', '💰', '🏳‍🌈', '💋', '❤‍🔥', '🚀', '🦄', '💖', '👽', '😘']

affixes += list('🐳🐋💩🐉🐲🐐😈🍆💰💲🦍💸🧙')  # for entertainment

affixes = dict.fromkeys(affixes)

structure = {}

for key, data in s.items():
    data = {k: v for k, v, t in data}
    structure[key] = {}
    print(key)
    for affix in affixes:
        count = data.get(affix, 0)
        structure[key][affix] = count
        print(f'{affix}\t{count}')

json.dump(structure, open('structure.json', 'w'), indent=2, ensure_ascii=False)
