#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


DB_PATH = Path('.todo.json')


def load_items():
    if not DB_PATH.exists():
        return []
    try:
        data = json.loads(DB_PATH.read_text(encoding='utf-8'))
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    return []


def save_items(items):
    DB_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding='utf-8')


def add_item(text):
    items = load_items()
    items.append({'text': text, 'done': False})
    save_items(items)
    return len(items)


def get_display_items(show_all=True):
    items = load_items()
    if show_all:
        return list(enumerate(items, start=1))
    return [(i, item) for i, item in enumerate(items, start=1) if not item['done']]


def mark_done(index):
    items = load_items()
    if index < 1 or index > len(items):
        return False
    items[index - 1]['done'] = True
    save_items(items)
    return True


def toggle_done(index):
    items = load_items()
    if index < 1 or index > len(items):
        return False
    items[index - 1]['done'] = not items[index - 1]['done']
    save_items(items)
    return True


def remove_item(index):
    items = load_items()
    if index < 1 or index > len(items):
        return None
    removed = items.pop(index - 1)
    save_items(items)
    return removed


def clear_items():
    save_items([])


def main():
    parser = argparse.ArgumentParser(description='Simple TODO CLI')
    sub = parser.add_subparsers(dest='command', required=True)

    p_add = sub.add_parser('add', help='Add TODO')
    p_add.add_argument('text', help='TODO text')

    p_list = sub.add_parser('list', help='List TODO items')
    p_list.add_argument('--pending', action='store_true', help='Show only pending items')

    p_done = sub.add_parser('done', help='Mark TODO as done')
    p_done.add_argument('index', type=int, help='Item number')

    p_rm = sub.add_parser('rm', help='Remove TODO')
    p_rm.add_argument('index', type=int, help='Item number')

    sub.add_parser('clear', help='Remove all TODO items')

    args = parser.parse_args()

    if args.command == 'add':
        index = add_item(args.text)
        print(f'Added: [{index}] {args.text}')
    elif args.command == 'list':
        display_items = get_display_items(show_all=not args.pending)
        if not display_items:
            print('No TODO items.')
            return
        for i, item in display_items:
            mark = 'x' if item['done'] else ' '
            print(f"[{i}] [{mark}] {item['text']}")
    elif args.command == 'done':
        if mark_done(args.index):
            items = load_items()
            print(f"Done: [{args.index}] {items[args.index - 1]['text']}")
        else:
            print('Invalid item number.')
    elif args.command == 'rm':
        removed = remove_item(args.index)
        if removed is None:
            print('Invalid item number.')
        else:
            print(f"Removed: [{args.index}] {removed['text']}")
    elif args.command == 'clear':
        clear_items()
        print('Cleared all TODO items.')


if __name__ == '__main__':
    main()
