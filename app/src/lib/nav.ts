/** Simple reactive store for page title shown in the global header. */

let _title = '';
let _listeners: Array<() => void> = [];

export function setPageTitle(title: string) {
	_title = title;
	for (const fn of _listeners) fn();
}

export function getPageTitle(): string {
	return _title;
}

export function onTitleChange(fn: () => void): () => void {
	_listeners.push(fn);
	return () => {
		_listeners = _listeners.filter((l) => l !== fn);
	};
}
