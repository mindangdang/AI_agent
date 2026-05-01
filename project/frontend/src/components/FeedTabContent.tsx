import { useMutation } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Plus, Loader2, Zap, Folder, ArrowLeft } from 'lucide-react';
import { useEffect, useMemo, useState, type FormEvent } from 'react';

import type { SavedItem } from '../types/item';
import type { AppUser } from '../types/user';
import { FeedItemCard } from './FeedItemCard';

type FeedTabContentProps = {
  items: SavedItem[];
  onItemsChange: React.Dispatch<React.SetStateAction<SavedItem[]>>;
  onSelectItem: (item: SavedItem) => void;
  refreshItems: () => Promise<void>;
  refreshTaste: () => Promise<void>;
  user: AppUser | null;
};

export function FeedTabContent({
  items,
  onItemsChange,
  onSelectItem,
  refreshItems,
  refreshTaste,
  user,
}: FeedTabContentProps) {
  const [newUrl, setNewUrl] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [currentFolder, setCurrentFolder] = useState<string | null>(null);

  const factKeysToShow = ['title', 'price_info', 'location_text', 'time_info', 'key_details'];
  const categories = useMemo(
    () => ['All', ...Array.from(new Set(items.map((item) => item.category))).filter(Boolean)],
    [items]
  );
  const filteredItems = useMemo(
    () => (selectedCategory === 'All' ? items : items.filter((item) => item.category === selectedCategory)),
    [items, selectedCategory]
  );

  const folders = useMemo(() => {
    const subs = new Set<string>();
    filteredItems.forEach((item) => {
      if (item.sub_category) subs.add(item.sub_category);
    });
    return Array.from(subs);
  }, [filteredItems]);

  const itemsToDisplay = useMemo(() => {
    if (currentFolder) return filteredItems.filter((item) => item.sub_category === currentFolder);
    return filteredItems.filter((item) => !item.sub_category);
  }, [filteredItems, currentFolder]);

  useEffect(() => {
    if (!user) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/ws/${user.id}`;
    let ws: WebSocket;

    try {
      ws = new WebSocket(wsUrl);

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === "CRAWL_SUCCESS") {
            console.log("[웹소켓] CRAWL_SUCCESS 메시지 수신: ", data);
            // 웹소켓으로부터 최종 아이템 데이터를 받으면, 기존의 임시 아이템을 제거하고 새 아이템으로 교체합니다.
            onItemsChange((prev) => {
              // placeholder_id와 일치하는 임시 아이템을 찾아서 제거합니다.
              const filtered = prev.filter(item => item.id !== data.placeholder_id);
              console.log("id 일치여부 확인: ", prev.map(item => ({ id: item.id, placeholder_id: data.placeholder_id })));
              // 새로 받은 최종 아이템(data.items)을 배열의 맨 앞에 추가합니다.
              return [...(data.items || []), ...filtered];
            });
            // 전체 아이템을 다시 불러올 필요 없이, 취향 분석만 새로고침합니다.
            setCurrentFolder((prev) => prev === 'PROCESSING ' ? null : prev);
            void refreshTaste();
          } else if (data.type === "CRAWL_ERROR") {
            alert(data.message || "데이터를 가져오는 데 실패했습니다. 잠시 후 다시 시도해주세요.");
            // 에러 발생 시, 해당 임시 아이템을 피드에서 제거합니다.
            onItemsChange((prev) => prev.filter(item => item.id !== data.placeholder_id));
          }
        } catch (err) {
          console.error("웹소켓 메시지 파싱 오류:", err);
        }
      };
    } catch (err) {
      console.error("웹소켓 연결 에러:", err);
    }

    return () => {
      if (ws) ws.close();
    };
  }, [user, onItemsChange, refreshTaste]);

  const addItemMutation = useMutation({
    mutationFn: async ({ nextUrl, nextSessionId, userId }: { nextUrl: string; nextSessionId: string; userId: number }) => {
      const res = await fetch('/api/extract-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: nextUrl, session_id: nextSessionId, user_id: userId })
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Failed to analyze URL");
      }

      return {
        nextUrl,
        data: await res.json(),
      };
    },
    onSuccess: ({ data }) => {
      // 백그라운드 작업이 시작되면, 백엔드는 임시 아이템 정보를 응답으로 보내줍니다.
      if (data.success && Array.isArray(data.data) && data.data.length > 0) {
        // 이 임시 아이템을 UI에 먼저 표시하여 사용자에게 작업이 진행 중임을 알립니다.
        onItemsChange((prev) => [data.data, ...prev]);
      }
      // 입력 필드를 초기화합니다.
      setNewUrl("");
      setSessionId("");
      // 여기서는 refreshItems()를 호출하지 않습니다.
      // 최종 데이터는 웹소켓을 통해 받아와 상태를 업데이트할 것이기 때문입니다.
    },
    onError: (error: Error) => {
      console.error(error);
      alert(`분석 요청 중 오류가 발생했습니다: ${error.message}`);
    },
  });

  const deleteItemMutation = useMutation({
    mutationFn: async ({ id, userId }: { id: number; userId: number }) => {
      const res = await fetch(`/api/items/${id}?user_id=${userId}`, { method: 'DELETE' });

      if (!res.ok) {
        throw new Error('Failed to delete item');
      }

      return id;
    },
    onMutate: async ({ id }) => {
      const previousItems = items;
      onItemsChange((currentItems) => currentItems.filter((item) => item.id !== id));
      return { previousItems };
    },
    onError: (error, _variables, context) => {
      console.error('Delete failed:', error);
      if (context?.previousItems) {
        onItemsChange(context.previousItems);
      }
      alert('삭제 중 오류가 발생했습니다.');
    },
  });

  const handleAddItem = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!newUrl || !user) return;
    await addItemMutation.mutateAsync({
      nextSessionId: sessionId,
      nextUrl: newUrl,
      userId: user.id,
    });
  };

  const handleDelete = async (id: number) => {
    if (!user) return;
    const shouldDelete = window.confirm('정말로 삭제하십니까?');
    if (!shouldDelete) return;
    await deleteItemMutation.mutateAsync({ id, userId: user.id });
  };

  return (
    <motion.div
      key="feed"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="space-y-8"
    >
      <header className="flex flex-col xl:flex-row xl:items-end justify-between gap-6">
        <div>
          <h2 className="text-4xl font-black tracking-tighter uppercase">My POSE! Feed</h2>
          <p className="text-gray-500 font-medium mt-1">Capture the vibes that define you.</p>
        </div>
        <form onSubmit={handleAddItem} className="flex flex-col sm:flex-row gap-2 items-end w-full xl:w-auto">
          <div className="flex-1 w-full xl:w-64 space-y-1.5">
            <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest">URL or Product Name</label>
            <input
              type="url"
              placeholder="Paste link..."
              value={newUrl}
              onChange={(e) => setNewUrl(e.target.value)}
              className="w-full px-4 py-3 bg-gray-50 border-none rounded-2xl focus:outline-none focus:ring-2 focus:ring-black text-sm font-medium transition-all"
            />
          </div>
          <div className="w-full sm:w-48 space-y-1.5">
            <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Session ID</label>
            <input
              type="password"
              placeholder="sessionid"
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
              className="w-full px-4 py-3 bg-gray-50 border-none rounded-2xl focus:outline-none focus:ring-2 focus:ring-black text-sm font-medium transition-all"
            />
          </div>
          <button
            disabled={addItemMutation.isPending}
            className="w-full sm:w-auto px-8 py-3 bg-black text-white rounded-2xl hover:bg-gray-800 hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-50 disabled:transform-none transition-all flex items-center justify-center gap-2 text-sm font-black tracking-widest uppercase h-[44px]"
          >
            {addItemMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            Add
          </button>
        </form>
      </header>

      {items.length > 0 && (
        <div className="flex flex-wrap gap-2 py-2">
          {categories.map((category) => (
            <button
              key={category}
            onClick={() => {
              setSelectedCategory(category);
              setCurrentFolder(null);
            }}
              className={[
                "px-5 py-2 rounded-full text-[11px] font-black uppercase tracking-widest transition-all",
                selectedCategory === category
                  ? "bg-black text-white shadow-md scale-105"
                  : "bg-gray-100 text-gray-500 hover:bg-gray-200",
              ].join(' ')}
            >
              {category}
            </button>
          ))}
        </div>
      )}

      <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4 items-stretch">
        {currentFolder && (
          <div className="col-span-full mb-2 flex items-center gap-4">
            <button
              onClick={() => setCurrentFolder(null)}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-full text-xs font-black uppercase tracking-widest transition-colors"
            >
              <ArrowLeft className="w-4 h-4" /> Back
            </button>
            <h3 className="text-xl font-black uppercase tracking-tight text-gray-800">{currentFolder}</h3>
          </div>
        )}

        {!currentFolder &&
          folders.map((folder) => (
            <motion.div
              layout
              key={`folder-${folder}`}
              onClick={() => setCurrentFolder(folder)}
              className="group relative flex aspect-[4/4.6] flex-col items-center justify-center overflow-hidden rounded-3xl border border-black/5 bg-gray-50 transition-all duration-300 cursor-pointer hover:-translate-y-1 hover:shadow-xl"
            >
              <Folder className="w-12 h-12 text-gray-300 group-hover:text-black transition-colors mb-3" fill="currentColor" />
              <h3 className="text-sm font-black text-gray-600 group-hover:text-black uppercase tracking-widest text-center px-4 line-clamp-2">
                {folder}
              </h3>
              <p className="text-[10px] font-bold text-gray-400 mt-2 bg-white px-3 py-1 rounded-full shadow-sm">
                {filteredItems.filter((i) => i.sub_category === folder).length} ITEMS
              </p>
            </motion.div>
          ))}

        {itemsToDisplay.map((item) => (
          <FeedItemCard
            key={item.id}
            factKeysToShow={factKeysToShow}
            item={item}
            onDelete={handleDelete}
            onSelect={() => onSelectItem(item)}
          />
        ))}
      </div>

      {items.length === 0 && !addItemMutation.isPending && (
        <div className="text-center py-32 bg-gray-50 rounded-[3rem] border-2 border-dashed border-gray-200">
          <div className="w-20 h-20 bg-white rounded-full flex items-center justify-center mx-auto mb-6 shadow-sm">
            <Zap className="w-10 h-10 text-yellow-400" fill="currentColor" />
          </div>
          <h3 className="text-2xl font-black tracking-tight mb-2">Strike your first POSE!</h3>
          <p className="text-gray-500 font-medium">인스타그램 링크를 넣고 나만의 바이브를 수집하세요.</p>
        </div>
      )}
    </motion.div>
  );
}
