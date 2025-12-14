import React, { useState, useRef, useEffect, useMemo } from 'react';
import {
    Play, Plus, Trash2, X, Zap, Clock,
    Terminal, Loader2, CheckSquare, Square, PlayCircle, RefreshCw, Copy
} from 'lucide-react';

interface SimulationMessage {
    id: string;
    text: string;
    tokensPerSec: number;
    firstTokenLatency: number;
}

interface ServerSimulatorProps {
    onSimulate: (text: string, rate: number, latency: number) => void;
    onSaveMessages?: (messages: SimulationMessage[]) => void;
    initialMessages?: SimulationMessage[];
}

const TAG_SUGGESTIONS = [
    { label: 'animate="mouth_open"', desc: 'Surprise', type: 'animate' },
    { label: 'animate="up_left_glance"', desc: 'Recalling image', type: 'animate' },
    { label: 'animate="up_right_glance"', desc: 'Visualizing', type: 'animate' },
    { label: 'animate="left_glance"', desc: 'Recalling sound', type: 'animate' },
    { label: 'animate="right_glance"', desc: 'Imagining dialogue', type: 'animate' },
    { label: 'animate="down_left_glance"', desc: 'Internal feelings', type: 'animate' },
    { label: 'animate="down_right_glance"', desc: 'Bad feelings', type: 'animate' },
    { label: 'animate="concentrate"', desc: 'Focus', type: 'animate' },
    { label: 'animate="giggle"', desc: 'Laugh', type: 'animate' },
    { label: 'animate="pout"', desc: 'Sulking', type: 'animate' },
    { label: 'animate="cheer"', desc: 'Excited', type: 'animate' },
    { label: 'animate="beg"', desc: 'Pleading', type: 'animate' },
    { label: 'animate="wink"', desc: 'Teasing', type: 'animate' },
    { label: 'animate="wave"', desc: 'Greeting', type: 'animate' },
    { label: 'emotion="blush"', desc: 'Embarrassed', type: 'emotion' },
    { label: 'emotion="happy"', desc: 'Excited', type: 'emotion' },
    { label: 'emotion="shy"', desc: 'Asking favors', type: 'emotion' },
    { label: 'emotion="sad"', desc: 'Malfunctioning', type: 'emotion' },
    { label: 'emotion="proud"', desc: 'Achievement', type: 'emotion' },
    { label: 'emotion="determination"', desc: 'Helping', type: 'emotion' },
    { label: 'emotion="anxiety"', desc: 'Nervous', type: 'emotion' },
    { label: 'emotion="smug"', desc: 'Self-satisfaction', type: 'emotion' },
    { label: 'emotion="suprise"', desc: 'Astonished', type: 'emotion' },
    { label: 'think', desc: 'Thinking block', type: 'tag', value: '<think></think>', cursorOffset: 7 },
];

export const ServerSimulator: React.FC<ServerSimulatorProps> = ({ onSimulate, onSaveMessages, initialMessages }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<SimulationMessage[]>([]);
    const [isSimulating, setIsSimulating] = useState(false);
    const [simulatingId, setSimulatingId] = useState<string | null>(null);

    const [inputText, setInputText] = useState("");
    const [rate, setRate] = useState(25);
    const [latency, setLatency] = useState(0.5);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const [editingId, setEditingId] = useState<string | null>(null);
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
    const [hoveredId, setHoveredId] = useState<string | null>(null);

    const [showSuggestions, setShowSuggestions] = useState(false);
    const [suggestionFilter, setSuggestionFilter] = useState("");
    const [suggestionTriggerPos, setSuggestionTriggerPos] = useState<number | null>(null);
    const [suggestionTriggerChar, setSuggestionTriggerChar] = useState<string | null>(null);
    const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(0);
    const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0 });
    const suggestionsRef = useRef<HTMLDivElement>(null);
    const textareaContainerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (initialMessages && initialMessages.length > 0) {
            setMessages(initialMessages);
        }
    }, [initialMessages]);

    useEffect(() => {
        if (messages.length > 0 && onSaveMessages) {
            onSaveMessages(messages);
        }
    }, [messages, onSaveMessages]);

    const filteredSuggestions = useMemo(() => {
        if (!suggestionFilter) return TAG_SUGGESTIONS;
        const lower = suggestionFilter.toLowerCase();
        return TAG_SUGGESTIONS.filter(
            t => t.label.toLowerCase().includes(lower) || t.desc.toLowerCase().includes(lower)
        );
    }, [suggestionFilter]);

    useEffect(() => {
        setSelectedSuggestionIndex(0);
    }, [filteredSuggestions]);

    const insertTagAtPosition = (tag: typeof TAG_SUGGESTIONS[0], triggerPos: number) => {
        if (!textareaRef.current) return;

        const textarea = textareaRef.current;
        const currentPos = textarea.selectionStart;
        const text = inputText;

        const before = text.substring(0, triggerPos);
        const after = text.substring(currentPos);

        let insertValue: string;
        let cursorOffset: number;

        if (tag.type === 'tag') {
            insertValue = tag.value || `<${tag.label}></${tag.label}>`;
            cursorOffset = tag.cursorOffset || insertValue.length;
        } else {
            insertValue = `|${tag.label}|`;
            cursorOffset = insertValue.length;
        }

        const newText = before + insertValue + after;
        setInputText(newText);

        setShowSuggestions(false);
        setSuggestionFilter("");
        setSuggestionTriggerPos(null);

        setTimeout(() => {
            textarea.focus();
            const newPos = triggerPos + cursorOffset;
            textarea.setSelectionRange(newPos, newPos);
        }, 10);
    };

    const getCaretCoordinates = (textarea: HTMLTextAreaElement, position: number) => {
        const div = document.createElement('div');
        const span = document.createElement('span');
        const computed = window.getComputedStyle(textarea);

        const properties = [
            'fontFamily', 'fontSize', 'fontWeight', 'fontStyle',
            'letterSpacing', 'textTransform', 'wordSpacing', 'textIndent',
            'paddingTop', 'paddingRight', 'paddingBottom', 'paddingLeft',
            'borderTopWidth', 'borderRightWidth', 'borderBottomWidth', 'borderLeftWidth',
            'lineHeight', 'whiteSpace'
        ];

        div.style.position = 'absolute';
        div.style.visibility = 'hidden';
        div.style.whiteSpace = 'pre-wrap';
        div.style.wordWrap = 'break-word';
        div.style.overflow = 'hidden';
        div.style.width = `${textarea.offsetWidth}px`;
        div.style.height = 'auto';

        properties.forEach(prop => {
            (div.style as any)[prop] = computed.getPropertyValue(
                prop.replace(/([A-Z])/g, '-$1').toLowerCase()
            );
        });

        const textBefore = textarea.value.substring(0, position);
        div.textContent = textBefore;

        span.textContent = textarea.value.substring(position) || '.';
        div.appendChild(span);

        document.body.appendChild(div);

        const spanRect = span.getBoundingClientRect();
        const divRect = div.getBoundingClientRect();

        let top = spanRect.top - divRect.top - textarea.scrollTop;
        let left = spanRect.left - divRect.left;

        left = Math.max(0, Math.min(left, textarea.offsetWidth - 290));

        document.body.removeChild(div);

        return { top: Math.max(20, top), left };
    };

    const closeSuggestions = () => {
        setShowSuggestions(false);
        setSuggestionTriggerPos(null);
        setSuggestionTriggerChar(null);
        setSuggestionFilter("");
    };

    const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const newText = e.target.value;
        const cursorPos = e.target.selectionStart;
        setInputText(newText);

        if (suggestionTriggerPos !== null && suggestionTriggerChar !== null) {
            const triggerStillExists = newText[suggestionTriggerPos] === suggestionTriggerChar;
            const cursorAfterTrigger = cursorPos > suggestionTriggerPos;

            if (!triggerStillExists || !cursorAfterTrigger) {
                closeSuggestions();
                return;
            }

            const textAfterTrigger = newText.substring(suggestionTriggerPos + 1, cursorPos);

            if (textAfterTrigger.includes(' ') || textAfterTrigger.includes('\n') ||
                textAfterTrigger.includes('|') || textAfterTrigger.includes('>')) {
                closeSuggestions();
            } else {
                setSuggestionFilter(textAfterTrigger);
                if (textareaRef.current) {
                    const coords = getCaretCoordinates(textareaRef.current, cursorPos);
                    setDropdownPosition({ top: coords.top + 24, left: coords.left });
                }
            }
            return;
        }

        const charBeforeCursor = newText[cursorPos - 1];

        if (charBeforeCursor === '|' || charBeforeCursor === '<') {
            setShowSuggestions(true);
            setSuggestionTriggerPos(cursorPos - 1);
            setSuggestionTriggerChar(charBeforeCursor);
            setSuggestionFilter("");
            setSelectedSuggestionIndex(0);

            if (textareaRef.current) {
                const coords = getCaretCoordinates(textareaRef.current, cursorPos);
                setDropdownPosition({ top: coords.top + 24, left: coords.left });
            }
        }
    };

    const handleTextareaKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (!showSuggestions || filteredSuggestions.length === 0) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            setSelectedSuggestionIndex(prev =>
                prev < filteredSuggestions.length - 1 ? prev + 1 : 0
            );
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setSelectedSuggestionIndex(prev =>
                prev > 0 ? prev - 1 : filteredSuggestions.length - 1
            );
        } else if (e.key === 'Enter' || e.key === 'Tab') {
            e.preventDefault();
            if (suggestionTriggerPos !== null) {
                insertTagAtPosition(filteredSuggestions[selectedSuggestionIndex], suggestionTriggerPos);
            }
        } else if (e.key === 'Escape') {
            closeSuggestions();
        } else if (e.key === 'Backspace') {
            if (suggestionTriggerPos !== null && textareaRef.current) {
                const cursorPos = textareaRef.current.selectionStart;
                if (cursorPos <= suggestionTriggerPos + 1) {
                    setTimeout(() => closeSuggestions(), 0);
                }
            }
        }
    };

    const insertTag = (tag: string) => {
        const tagData = TAG_SUGGESTIONS.find(t => (t.value || t.label) === tag);

        let value: string;
        let cursorOffset: number;

        if (tagData?.type === 'tag') {
            value = tagData.value || `<${tag}></${tag}>`;
            cursorOffset = tagData.cursorOffset || value.length;
        } else {
            value = `|${tag}|`;
            cursorOffset = value.length;
        }

        if (textareaRef.current) {
            const start = textareaRef.current.selectionStart;
            const end = textareaRef.current.selectionEnd;
            const text = inputText;
            const before = text.substring(0, start);
            const after = text.substring(end, text.length);

            setInputText(before + value + after);

            setTimeout(() => {
                textareaRef.current?.focus();
                const newPos = start + cursorOffset;
                textareaRef.current?.setSelectionRange(newPos, newPos);
            }, 10);
        } else {
            setInputText(prev => prev + value);
        }
    };

    const loadMessageForEdit = (msg: SimulationMessage) => {
        setInputText(msg.text);
        setRate(msg.tokensPerSec);
        setLatency(msg.firstTokenLatency);
        setEditingId(msg.id);
        textareaRef.current?.focus();
    };

    const addOrUpdateMessage = () => {
        if (!inputText.trim()) return;

        if (editingId) {
            setMessages(messages.map(m =>
                m.id === editingId
                    ? { ...m, text: inputText, tokensPerSec: rate, firstTokenLatency: latency }
                    : m
            ));
            setEditingId(null);
        } else {
            const newMessage: SimulationMessage = {
                id: Date.now().toString(),
                text: inputText,
                tokensPerSec: rate,
                firstTokenLatency: latency
            };
            setMessages([...messages, newMessage]);
        }
        setInputText("");
    };

    const cancelEdit = () => {
        setEditingId(null);
        setInputText("");
        setRate(25);
        setLatency(0.5);
    };

    const removeMessage = (id: string) => {
        setMessages(messages.filter(m => m.id !== id));
        if (editingId === id) {
            cancelEdit();
        }
        setSelectedIds(prev => {
            const newSet = new Set(prev);
            newSet.delete(id);
            return newSet;
        });
    };

    const toggleSelect = (id: string) => {
        setSelectedIds(prev => {
            const newSet = new Set(prev);
            if (newSet.has(id)) {
                newSet.delete(id);
            } else {
                newSet.add(id);
            }
            return newSet;
        });
    };

    const toggleSelectAll = () => {
        if (selectedIds.size === messages.length) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(messages.map(m => m.id)));
        }
    };

    const deleteSelected = () => {
        setMessages(messages.filter(m => !selectedIds.has(m.id)));
        if (editingId && selectedIds.has(editingId)) {
            cancelEdit();
        }
        setSelectedIds(new Set());
    };

    const duplicateMessage = (msg: SimulationMessage) => {
        const newMessage: SimulationMessage = {
            id: Date.now().toString(),
            text: msg.text,
            tokensPerSec: msg.tokensPerSec,
            firstTokenLatency: msg.firstTokenLatency
        };
        const index = messages.findIndex(m => m.id === msg.id);
        const newMessages = [...messages];
        newMessages.splice(index + 1, 0, newMessage);
        setMessages(newMessages);
    };

    const playMessage = (msg: SimulationMessage) => {
        if (isSimulating) return;

        setIsSimulating(true);
        setSimulatingId(msg.id);

        onSimulate(msg.text, msg.tokensPerSec, msg.firstTokenLatency);

        const estimatedChars = msg.text.length;
        const charsPerToken = 4;
        const estimatedTokens = estimatedChars / charsPerToken;
        const streamTime = estimatedTokens / msg.tokensPerSec;
        const totalTime = (msg.firstTokenLatency + streamTime) * 1000 + 500;

        setTimeout(() => {
            setIsSimulating(false);
            setSimulatingId(null);
        }, totalTime);
    };

    const playAllQueue = async () => {
        if (isSimulating || messages.length === 0) return;

        for (const msg of messages) {
            await new Promise<void>((resolve) => {
                setIsSimulating(true);
                setSimulatingId(msg.id);

                onSimulate(msg.text, msg.tokensPerSec, msg.firstTokenLatency);

                const estimatedChars = msg.text.length;
                const charsPerToken = 4;
                const estimatedTokens = estimatedChars / charsPerToken;
                const streamTime = estimatedTokens / msg.tokensPerSec;
                const totalTime = (msg.firstTokenLatency + streamTime) * 1000 + 500;

                setTimeout(() => {
                    setIsSimulating(false);
                    setSimulatingId(null);
                    resolve();
                }, totalTime);
            });
        }
    };

    if (!isOpen) {
        return (
            <button
                onClick={() => setIsOpen(true)}
                className="fixed bottom-6 right-6 z-50 p-4 bg-gray-900 text-white rounded-full shadow-lg hover:bg-gray-800 transition-all hover:scale-105"
                title="Open Server Simulator"
            >
                <Terminal size={24} />
            </button>
        );
    }

    const isAllSelected = messages.length > 0 && selectedIds.size === messages.length;
    const hasSelection = selectedIds.size > 0;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
            <div className="bg-white w-[850px] h-[650px] rounded-2xl shadow-2xl flex overflow-hidden border border-gray-100 flex-col">

                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 bg-gray-50 border-b border-gray-100">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-100 text-blue-600 rounded-lg">
                            <Terminal size={20} />
                        </div>
                        <div>
                            <h2 className="font-bold text-gray-800">Server Simulator</h2>
                            <p className="text-xs text-gray-500">Test LLM responses & delays</p>
                        </div>
                    </div>
                    <button
                        onClick={() => setIsOpen(false)}
                        className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
                    >
                        <X size={20} />
                    </button>
                </div>

                <div className="flex flex-1 overflow-hidden">

                    {/* Left: Message Queue */}
                    <div className="w-1/3 bg-gray-50/50 border-r border-gray-100 flex flex-col">
                        <div className="p-4 border-b border-gray-100 font-medium text-xs text-gray-500 uppercase tracking-wider">
                            <div className="flex justify-between items-center">
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={toggleSelectAll}
                                        className="p-1 hover:bg-gray-200 rounded transition-colors"
                                        title={isAllSelected ? "Deselect all" : "Select all"}
                                    >
                                        {isAllSelected ? (
                                            <CheckSquare size={14} className="text-blue-600" />
                                        ) : (
                                            <Square size={14} className="text-gray-400" />
                                        )}
                                    </button>
                                    <span>Message Queue</span>
                                </div>
                                <span className="bg-gray-200 text-gray-600 px-2 rounded-full">{messages.length}</span>
                            </div>

                            {hasSelection && (
                                <div className="flex gap-2 mt-2 pt-2 border-t border-gray-200">
                                    <button
                                        onClick={deleteSelected}
                                        className="flex-1 text-[10px] px-2 py-1 bg-red-50 text-red-600 rounded hover:bg-red-100 transition-colors flex items-center justify-center gap-1"
                                    >
                                        <Trash2 size={10} />
                                        Delete ({selectedIds.size})
                                    </button>
                                    <button
                                        onClick={playAllQueue}
                                        disabled={isSimulating}
                                        className="flex-1 text-[10px] px-2 py-1 bg-green-50 text-green-600 rounded hover:bg-green-100 disabled:opacity-50 transition-colors flex items-center justify-center gap-1"
                                    >
                                        <PlayCircle size={10} />
                                        Play All
                                    </button>
                                </div>
                            )}
                        </div>

                        <div className="flex-1 overflow-y-auto p-2 space-y-2">
                            {messages.length === 0 && (
                                <div className="text-center py-10 text-gray-400 text-sm italic">
                                    No messages queued.
                                    <br />Add one to get started.
                                </div>
                            )}

                            {messages.map(msg => (
                                <div
                                    key={msg.id}
                                    onClick={() => loadMessageForEdit(msg)}
                                    onMouseEnter={() => setHoveredId(msg.id)}
                                    onMouseLeave={() => setHoveredId(null)}
                                    className={`group bg-white p-3 rounded-xl border shadow-sm transition-all cursor-pointer ${simulatingId === msg.id
                                        ? 'border-green-400 bg-green-50'
                                        : editingId === msg.id
                                            ? 'border-blue-400 bg-blue-50 ring-2 ring-blue-200'
                                            : 'border-gray-200 hover:border-blue-200 hover:shadow-md'
                                        }`}
                                >
                                    <div className="flex justify-between items-start mb-2">
                                        <div className="flex items-center gap-2">
                                            {(hoveredId === msg.id || selectedIds.has(msg.id)) && (
                                                <button
                                                    onClick={(e) => { e.stopPropagation(); toggleSelect(msg.id); }}
                                                    className="p-0.5 hover:bg-gray-100 rounded transition-all"
                                                >
                                                    {selectedIds.has(msg.id) ? (
                                                        <CheckSquare size={14} className="text-blue-600" />
                                                    ) : (
                                                        <Square size={14} className="text-gray-400" />
                                                    )}
                                                </button>
                                            )}
                                            <span className="text-[10px] font-mono bg-gray-100 px-1.5 py-0.5 rounded text-gray-500">
                                                {msg.tokensPerSec} t/s • {msg.firstTokenLatency}s
                                            </span>
                                        </div>
                                        <div className="flex gap-1">
                                            <button
                                                onClick={(e) => { e.stopPropagation(); duplicateMessage(msg); }}
                                                className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-all opacity-0 group-hover:opacity-100"
                                                title="Duplicate"
                                            >
                                                <Copy size={12} />
                                            </button>
                                            <button
                                                onClick={(e) => { e.stopPropagation(); playMessage(msg); }}
                                                disabled={isSimulating}
                                                className={`p-1.5 rounded transition-all ${isSimulating ? 'opacity-50 cursor-not-allowed' : 'text-green-600 hover:bg-green-50'}`}
                                                title={isSimulating ? "Simulation in progress" : "Play Message"}
                                            >
                                                {simulatingId === msg.id ? (
                                                    <Loader2 size={14} className="animate-spin" />
                                                ) : (
                                                    <Play size={14} />
                                                )}
                                            </button>
                                            <button
                                                onClick={(e) => { e.stopPropagation(); removeMessage(msg.id); }}
                                                disabled={simulatingId === msg.id}
                                                className="p-1.5 text-red-400 hover:bg-red-50 rounded disabled:opacity-50"
                                            >
                                                <Trash2 size={14} />
                                            </button>
                                        </div>
                                    </div>
                                    <p className="text-sm text-gray-700 line-clamp-3 font-medium leading-relaxed">
                                        {msg.text}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Right: Input Form */}
                    <div className="flex-1 flex flex-col bg-white">
                        <div className="p-6 flex-1 flex flex-col overflow-y-auto">
                            <div className="flex items-center justify-between mb-2">
                                <label className="text-xs font-bold text-gray-500 uppercase tracking-wider block">
                                    {editingId ? 'Edit Message' : 'New Simulation Message'}
                                </label>
                                {editingId && (
                                    <button
                                        onClick={cancelEdit}
                                        className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1"
                                    >
                                        <RefreshCw size={10} />
                                        Cancel Edit
                                    </button>
                                )}
                            </div>

                            <div ref={textareaContainerRef} className="relative flex-1 flex flex-col">
                                <textarea
                                    ref={textareaRef}
                                    value={inputText}
                                    onChange={handleTextareaChange}
                                    onKeyDown={handleTextareaKeyDown}
                                    onBlur={() => setTimeout(() => closeSuggestions(), 150)}
                                    placeholder="Type server message here... Use |animate=...| or <think> tags."
                                    className={`flex-1 w-full p-4 bg-gray-50 border rounded-xl focus:ring-2 transition-all resize-none text-sm leading-relaxed font-mono ${editingId
                                        ? 'border-blue-300 focus:border-blue-500 focus:ring-blue-100'
                                        : 'border-gray-200 focus:border-blue-500 focus:ring-blue-100'
                                        }`}
                                    style={{ minHeight: '150px' }}
                                />

                                {/* Intellisense Dropdown */}
                                {showSuggestions && filteredSuggestions.length > 0 && (
                                    <div
                                        ref={suggestionsRef}
                                        className="absolute z-50 w-80 max-h-52 overflow-y-auto bg-white border border-gray-200 rounded-lg shadow-2xl"
                                        style={{
                                            top: `${Math.min(dropdownPosition.top + 20, 120)}px`,
                                            left: `${Math.max(4, Math.min(dropdownPosition.left, 200))}px`,
                                        }}
                                        onMouseDown={(e) => e.preventDefault()}
                                    >
                                        <div className="sticky top-0 bg-gray-50 px-3 py-1.5 border-b border-gray-100 text-[10px] text-gray-400 uppercase tracking-wider">
                                            {suggestionTriggerChar === '<' ? 'XML Tags' : 'Inline Tags'} • {filteredSuggestions.length} results
                                        </div>
                                        {filteredSuggestions.map((tag, idx) => (
                                            <button
                                                key={idx}
                                                onClick={() => suggestionTriggerPos !== null && insertTagAtPosition(tag, suggestionTriggerPos)}
                                                className={`w-full text-left px-3 py-2 text-sm flex items-center justify-between transition-colors ${idx === selectedSuggestionIndex
                                                    ? 'bg-blue-100 text-blue-700'
                                                    : 'hover:bg-gray-50'
                                                    }`}
                                            >
                                                <span className="font-mono text-xs truncate flex-1">{tag.label}</span>
                                                <span className="text-gray-400 text-xs ml-2 whitespace-nowrap">{tag.desc}</span>
                                            </button>
                                        ))}
                                    </div>
                                )}

                                {/* Tag Hints */}
                                <div className="mt-3 border border-gray-100 rounded-lg p-3 bg-gray-50/50">
                                    <div className="text-xs font-bold text-gray-400 mb-2 flex items-center gap-1">
                                        <Zap size={12} />
                                        Quick Insert (Click to add)
                                    </div>
                                    <div className="flex flex-wrap gap-2 max-h-[100px] overflow-y-auto pr-1">
                                        {TAG_SUGGESTIONS.map((tag, idx) => (
                                            <button
                                                key={idx}
                                                onClick={() => insertTag(tag.value || tag.label)}
                                                className="text-[10px] px-2 py-1 bg-white border border-gray-200 rounded-md hover:border-blue-300 hover:text-blue-600 hover:shadow-sm transition-all text-left flex items-center gap-1"
                                            >
                                                <span className="font-mono text-gray-600">{tag.label.replace('animate=', '').replace('emotion=', '')}</span>
                                                <span className="text-gray-300">|</span>
                                                <span className="text-gray-400">{tag.desc}</span>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4 mt-6">
                                <div className="space-y-1">
                                    <label className="flex items-center justify-between text-xs font-medium text-gray-500">
                                        <span className="flex items-center gap-1"><Zap size={12} /> Tokens / Sec</span>
                                        <span className="text-gray-900 font-bold">{rate}</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="1" max="100"
                                        value={rate}
                                        onChange={(e) => setRate(Number(e.target.value))}
                                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                                    />
                                </div>

                                <div className="space-y-1">
                                    <label className="flex items-center justify-between text-xs font-medium text-gray-500">
                                        <span className="flex items-center gap-1"><Clock size={12} /> First Token Latency</span>
                                        <span className="text-gray-900 font-bold">{latency}s</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="0" max="5" step="0.1"
                                        value={latency}
                                        onChange={(e) => setLatency(Number(e.target.value))}
                                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                                    />
                                </div>
                            </div>

                            <div className="flex gap-3 mt-6 pt-4 border-t border-gray-100">
                                <button
                                    onClick={() => { setInputText(""); if (editingId) cancelEdit(); }}
                                    className="px-4 py-2 text-gray-500 hover:bg-gray-100 rounded-lg text-sm font-medium transition-colors"
                                >
                                    Clear
                                </button>
                                <button
                                    onClick={addOrUpdateMessage}
                                    disabled={!inputText.trim()}
                                    className={`flex-1 rounded-lg py-2.5 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 shadow-lg hover:shadow-xl hover:-translate-y-0.5 ${editingId
                                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                                        : 'bg-gray-900 text-white hover:bg-gray-800'
                                        }`}
                                >
                                    {editingId ? (
                                        <>
                                            <RefreshCw size={16} />
                                            Update Message
                                        </>
                                    ) : (
                                        <>
                                            <Plus size={16} />
                                            Add Message to Queue
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
