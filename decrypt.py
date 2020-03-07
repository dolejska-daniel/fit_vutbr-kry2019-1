import base64
import random
from collections import Counter
from itertools import product


def collect_characters(messages: [[int]]) -> dict:
    # list of lists of characters at given indices in all messages
    characters = {i: [] for i in range(400)}
    message_count = len(messages)

    # for each provided message
    for message_index in range(message_count):
        print("\rCollecting characters from all messages... message {:3d}/{:3d}".format(message_index, message_count),
              end="", flush=True)

        message = messages[message_index]
        # add character from current message at given indices
        # to list of all characters at given indices in all messages
        for char_index in range(len(message)):
            characters[char_index].append(message[char_index])

    return characters


def count_characters(characters):
    print("\rProcessing and sorting collected counts...", end="", flush=True)
    character_counts = {}
    for char_index in characters.keys():
        sample_count = len(characters[char_index])
        character_counts[char_index] = Counter(characters[char_index])

        counts = []
        for char, count in character_counts[char_index].items():
            counts.append((char, (count, count / sample_count)))

        character_counts[char_index] = dict(sorted(counts, key=lambda x: x[1][1], reverse=True))


def create_xor_table() -> {set}:
    print("\rCreating XOR lookup table...", end="", flush=True)
    table = {xor: [] for xor in range(2 ** 8)}
    for x in range(2 ** 8):
        for y in range(2 ** 8):
            t = (chr(x), chr(y))
            table[x ^ y].append(t)

    for xor in table.keys():
        table[xor] = set(table[xor])

    return table


def find_possible_key_chars(xor_table, xor_chars, extended=False):
    key_chars = {
        ch1
        for ch1, ch2 in xor_table[xor_chars.pop(0)]
        if (extended and ord(ch2) < 128 and ch2.isprintable())
            or (ord(ch2) < 128 and (ch2.isalnum() or ch2 == " "))
    }

    for xor_char in xor_chars:
        next_key_chars = {
            ch1
            for ch1, ch2 in xor_table[xor_char]
            if (extended and ord(ch2) < 128 and ch2.isprintable())
                or (ord(ch2) < 128 and (ch2.isalnum() or ch2 == " "))
        }

        new_key_chars = key_chars.intersection(next_key_chars)
        if len(new_key_chars) == 0 and not extended:
            return find_possible_key_chars(xor_table, xor_chars, extended=True)
        else:
            key_chars = new_key_chars

    return key_chars


def decrypt_message(message: [int], message_key: [str]) -> [int]:
    result = []
    for key_char_index, key_char in enumerate(message_key):
        result.append(message[key_char_index] ^ ord(key_char))

    return result


def message_to_str(message: [int]) -> str:
    return "".join([chr(ch) for ch in message])


#===========================================================================dd==

def main():
    print("\rLoading messages from file...", end="", flush=True)
    with open("messages10k.txt", "r") as f:
        encoded_messages = f.readlines()

    if len(encoded_messages) < 1:
        print("\rThere is not enough messages to efficiently recover the key!")
        exit(1)

    print("\rDecoding messages from base64...", end="", flush=True)
    messages = [base64.standard_b64decode(m) for m in encoded_messages]

    chars_at_index = collect_characters(messages)
    xor_table = create_xor_table()

    decrypt_size = 20
    first_unprocessed_message_char_index = 0
    target_message = messages[0]  # TODO: LONGEST message

    result_key = ""
    result_message = ""
    choices = []

    while first_unprocessed_message_char_index < len(target_message):
        message_from_index = first_unprocessed_message_char_index

        possible_key_chars = []
        for index in range(message_from_index, min(len(target_message), message_from_index + 2 * decrypt_size)):
            print("\rRecovering the key... {:3d}/{:3d} (you may be prompted to select correct words)".format(index, len(target_message)), end="", flush=True)
            chars = chars_at_index[index]
            possible_chars = list(find_possible_key_chars(xor_table, chars))
            possible_key_chars.append(possible_chars)

            if len(possible_chars) == 1 and index >= message_from_index + decrypt_size:
                decrypted_char = message_to_str(decrypt_message(target_message[index:index + 1], possible_chars[0]))
                if " " == decrypted_char:
                    break

        first_possible_key = next(product(*possible_key_chars))
        relevant_message_chars = target_message[message_from_index:message_from_index + len(first_possible_key)]
        first_possible_text = message_to_str(decrypt_message(relevant_message_chars, first_possible_key))
        text_space_relative_indices = [
            index
            for index, char in enumerate(first_possible_text)
            if char == " " and len(possible_key_chars[index]) == 1
        ]

        words = []
        last_word_end_index = 0
        if len(text_space_relative_indices) > 0:
            for space_index in text_space_relative_indices:
                from_index = last_word_end_index
                to_index = last_word_end_index + space_index + 1

                cipher_word = relevant_message_chars[from_index:to_index]
                relevant_key_chars = possible_key_chars[from_index:to_index]

                w = (
                    cipher_word,
                    list(product(*relevant_key_chars)),
                    first_unprocessed_message_char_index + from_index,
                    first_unprocessed_message_char_index + to_index
                )
                words.append(w)

                last_word_end_index = to_index

            first_unprocessed_message_char_index += max(text_space_relative_indices) + 1

        else:
            w = (
                relevant_message_chars,
                list(product(*possible_key_chars)),
                first_unprocessed_message_char_index,
                len(target_message)
            )
            words.append(w)
            first_unprocessed_message_char_index += len(target_message)

        for cipher_word, keys, start_index, end_index in words:
            if len(keys) > 1:
                print("\rUnsure about recovered key for word at index {:d}-{:d}:".format(start_index, end_index))
                format_line = "".join(["-" for _ in range(len(cipher_word) + 2)])
                print("     +{:s}".format(format_line))
                for variant_index, key in enumerate(keys, start=1):
                    word = message_to_str(decrypt_message(cipher_word, key))
                    print("{:>4} | {:s}".format(variant_index, word))
                print("     +{:s}".format(format_line))

                selected_variant = int(input(" ^ Please select correct version of the word: "))
                selected_key = keys[selected_variant - 1]

                choice = (start_index, end_index, selected_key, keys)
                choices.append(choice)

                result_message += message_to_str(decrypt_message(cipher_word, selected_key))
                k = "".join(selected_key)
                result_key += k

            else:
                result_message += message_to_str(decrypt_message(cipher_word, keys[0]))
                result_key += "".join(keys[0])

        # print(result_message)
        # print(result_key)

    print()
    print("\rSaving key to kex.txt...", end="", flush=True)
    with open("key.txt", "wb") as f:
        f.write(result_key.encode())

    print()
    print("\rValidating recovered key against other messages...", end="", flush=True)

    random_messages = random.choices(messages, k=2)

    for start_index, end_index, selected_key, keys in choices:
        cipher_words = [
            m[start_index:end_index]
            for m in random_messages
        ]
        print("\rValidating word choice at index {:d}-{:d}:".format(start_index, end_index))
        cell_width = end_index - start_index + 2
        format_line = "".join(["-" for _ in range(cell_width)])
        print("     +{:s}".format(format_line))
        for variant_index, key in enumerate(keys, start=1):
            target_cipher_word = target_message[start_index:end_index]
            target_word = message_to_str(decrypt_message(target_cipher_word, key))
            print("{:>4} | {:s} {:s}".format(variant_index, target_word,
                                             "<= SELECTED VARIANT" if key == selected_key else ""))
            for cipher_word in cipher_words:
                word = message_to_str(decrypt_message(cipher_word, key))
                print("     | {:s}".format(word))
            print("     +{:s}".format(format_line))

        selected_variant = int(input(" ^ Please select variant where all the words are correct: "))
        newly_selected_key = keys[selected_variant - 1]

        if newly_selected_key != selected_key:
            result_key[start_index:end_index] = newly_selected_key

    print("\rValidation completed, saving key to kex.txt...", end="", flush=True)
    with open("key.txt", "wb") as f:
        f.write(result_key.encode())

    print("\rProcess finished, key recovered!")

if __name__ == '__main__':
    main()
