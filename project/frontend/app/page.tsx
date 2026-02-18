'use client';

import { AnimatePresence, motion } from 'framer-motion';
import {
  BadgeDollarSign,
  CalendarClock,
  Check,
  HeartHandshake,
  Instagram,
  LoaderCircle,
  MapPin,
  Search,
  Sparkles,
  Tag,
  X
} from 'lucide-react';
import { useMemo, useState } from 'react';
import Masonry from 'react-masonry-css';

type Tab = 'archive' | 'analytics' | 'discovery' | 'search';
type Category = 'ALL' | 'PLACE' | 'PRODUCT' | 'MEDIA';

type Item = {
  id: number;
  title: string;
  category: Exclude<Category, 'ALL'>;
  image: string;
  vibe: string;
  price?: string;
  location?: string;
};

const items: Item[] = [
  {
    id: 1,
    title: 'Quiet Wood Cafe',
    category: 'PLACE',
    image: 'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?q=80&w=1000',
    vibe: '#차분한_우드톤',
    price: '₩7,000 ~',
    location: '서울 연남'
  },
  {
    id: 2,
    title: 'Minimal Trench Coat',
    category: 'PRODUCT',
    image: 'https://images.unsplash.com/photo-1543087903-1ac2ec7aa8c5?q=80&w=1000',
    vibe: '#도시적_미니멀',
    price: '₩189,000'
  },
  {
    id: 3,
    title: 'Rainy Night Film',
    category: 'MEDIA',
    image: 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=1000',
    vibe: '#비오는_밤_감성'
  },
  {
    id: 4,
    title: 'Riverside Book Spot',
    category: 'PLACE',
    image: 'https://images.unsplash.com/photo-1509021436665-8f07dbf5bf1d?q=80&w=1000',
    vibe: '#비오는_날_독서',
    location: '서울 망원'
  },
  {
    id: 5,
    title: 'Vintage Speakers',
    category: 'PRODUCT',
    image: 'https://images.unsplash.com/photo-1520170350707-b2da59970118?q=80&w=1000',
    vibe: '#레트로_하이파이',
    price: '₩430,000'
  },
  {
    id: 6,
    title: 'Indie Book Zine',
    category: 'MEDIA',
    image: 'https://images.unsplash.com/photo-1507842217343-583bb7270b66?q=80&w=1000',
    vibe: '#아날로그_무드'
  }
];

const recommendedVibes = [
  '#힙한_을지로_감성',
  '#차분한_우드톤',
  '#비오는_날_독서',
  '#로맨틱_시티팝',
  '#포근한_재즈바'
];

const breakpoints = { default: 4, 1200: 3, 768: 2, 500: 1 };

function MasonryCards({ source, onClick }: { source: Item[]; onClick?: (item: Item) => void }) {
  return (
    <Masonry breakpointCols={breakpoints} className="masonry-grid" columnClassName="masonry-grid_column">
      {source.map((item, idx) => (
        <motion.button
          key={item.id}
          onClick={() => onClick?.(item)}
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: idx * 0.03, duration: 0.4 }}
          className="glass mb-4 w-full overflow-hidden rounded-2xl text-left shadow-soft transition hover:scale-[1.01] hover:shadow-[0_16px_36px_rgba(180,130,80,0.22)]"
        >
          <img src={item.image} alt={item.title} className="h-auto w-full object-cover" />
          <div className="p-4">
            <div className="mb-1 text-sm text-amber-500">{item.category}</div>
            <h3 className="text-lg font-semibold">{item.title}</h3>
            <p className="mt-2 text-sm text-stone-600">{item.vibe}</p>
          </div>
        </motion.button>
      ))}
    </Masonry>
  );
}

export default function Home() {
  const [tab, setTab] = useState<Tab>('archive');
  const [category, setCategory] = useState<Category>('ALL');
  const [selected, setSelected] = useState<Item | null>(null);
  const [vibeInput, setVibeInput] = useState('');
  const [focused, setFocused] = useState(false);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState<Item[]>([]);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loginLoading, setLoginLoading] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const filtered = useMemo(() => {
    if (category === 'ALL') return items;
    return items.filter((i) => i.category === category);
  }, [category]);

  const runSearch = async () => {
    setLoading(true);
    await new Promise((r) => setTimeout(r, 1200));
    setSearched(items.filter((i) => (vibeInput ? i.vibe.includes(vibeInput.slice(0, 4)) : true)));
    setLoading(false);
  };

  const runInstagramLogin = async () => {
    setLoginLoading(true);
    await new Promise((r) => setTimeout(r, 1400));
    setIsLoggedIn(true);
    setLoginLoading(false);
    setShowLoginModal(false);
  };

  return (
    <main className="min-h-screen p-4 md:p-8">
      <div className="mx-auto max-w-7xl">
        <header className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="gradient-text text-4xl font-black tracking-tight">Vibe Search</h1>
            <p className="mt-2 text-stone-600">초개인화 AI 하이브리드 추천/검색 경험</p>
          </div>
          <button
            onClick={() => (isLoggedIn ? setIsLoggedIn(false) : setShowLoginModal(true))}
            className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition ${
              isLoggedIn
                ? 'bg-emerald-100 text-emerald-700 ring-1 ring-emerald-300 hover:bg-emerald-200'
                : 'bg-gradient-to-r from-amber-500 to-orange-400 text-white hover:opacity-95'
            }`}
          >
            {isLoggedIn ? <Check className="h-4 w-4" /> : <Instagram className="h-4 w-4" />}
            {isLoggedIn ? 'Instagram 연결됨 (로그아웃)' : '인스타그램으로 로그인'}
          </button>
        </header>

        <nav className="glass mb-8 flex flex-wrap gap-2 rounded-2xl p-2">
          {[
            ['archive', 'Archive'],
            ['analytics', 'Analytics'],
            ['discovery', 'Discovery Feed'],
            ['search', 'Hybrid Search']
          ].map(([key, label]) => (
            <button
              key={key}
              onClick={() => setTab(key as Tab)}
              className={`rounded-xl px-4 py-2 text-sm font-medium transition ${
                tab === key ? 'bg-amber-500 text-white' : 'text-stone-600 hover:bg-amber-100/70'
              }`}
            >
              {label}
            </button>
          ))}
        </nav>

        {tab === 'archive' && (
          <section>
            {!isLoggedIn && (
              <div className="mb-5 rounded-2xl border border-amber-300/70 bg-amber-100/70 p-4 text-sm text-amber-900">
                스크랩 기반 아카이브를 보려면 <b>인스타그램 로그인</b>이 필요합니다. 우측 상단 버튼을 눌러 연결해 주세요.
              </div>
            )}
            <div className="mb-6 flex flex-wrap gap-2">
              {(['ALL', 'PLACE', 'PRODUCT', 'MEDIA'] as Category[]).map((c) => (
                <button
                  key={c}
                  onClick={() => setCategory(c)}
                  className={`rounded-full px-4 py-2 text-sm ${
                    category === c ? 'bg-amber-200 text-stone-900' : 'glass text-stone-700'
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
            <MasonryCards source={filtered} onClick={setSelected} />
          </section>
        )}

        {tab === 'analytics' && (
          <section className="glass rounded-3xl p-8 md:p-14">
            <p className="text-sm uppercase tracking-[0.3em] text-stone-500">Your 2026 Vibe Wrapped</p>
            <h2 className="gradient-text mt-4 text-5xl font-extrabold md:text-7xl">CALM CITY CORE</h2>
            <div className="mt-10 grid gap-4 md:grid-cols-3">
              {[
                ['Top Mood', '차분한 우드톤'],
                ['Peak Time', '금요일 밤 10:00'],
                ['Most Saved', 'Book Cafe / Indie Film']
              ].map(([k, v]) => (
                <div key={k} className="rounded-2xl bg-amber-50/70 p-6">
                  <p className="text-xs uppercase tracking-wide text-stone-500">{k}</p>
                  <p className="mt-3 text-xl font-semibold">{v}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {tab === 'discovery' && (
          <section className="space-y-10">
            <div>
              <h2 className="mb-4 flex items-center gap-2 text-2xl font-bold">
                <Sparkles className="h-5 w-5 text-orange-400" />의외의 발견
              </h2>
              <MasonryCards source={[...items].reverse()} />
            </div>
            <div className="glass rounded-3xl p-6">
              <h3 className="mb-5 flex items-center gap-2 text-xl font-bold">
                <HeartHandshake className="text-orange-500" />Vibe Mixer
              </h3>
              <motion.div
                initial={{ scale: 0.92, opacity: 0 }}
                whileInView={{ scale: 1, opacity: 1 }}
                viewport={{ once: true }}
                className="mb-6 flex items-center justify-center gap-4"
              >
                <div className="grid h-20 w-20 place-content-center rounded-full bg-amber-200/90">Me</div>
                <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 5, ease: 'linear' }}>
                  <Sparkles className="text-amber-500" />
                </motion.div>
                <div className="grid h-20 w-20 place-content-center rounded-full bg-orange-200/80">Friend</div>
              </motion.div>
              <MasonryCards source={items.slice(1, 5)} />
            </div>
          </section>
        )}

        {tab === 'search' && (
          <section className="space-y-6">
            <div className="glass rounded-3xl p-5">
              <div className="mb-4 flex flex-wrap gap-2">
                {['📍 PLACE', '👕 PRODUCT', '🎬 MEDIA'].map((chip) => (
                  <button
                    key={chip}
                    className="rounded-full border border-amber-200/80 px-3 py-2 text-sm hover:bg-amber-100/70"
                  >
                    {chip}
                  </button>
                ))}
                <select className="rounded-full bg-amber-100/80 px-3 py-2 text-sm">
                  <option>지역</option>
                  <option>서울</option>
                  <option>부산</option>
                </select>
                <select className="rounded-full bg-amber-100/80 px-3 py-2 text-sm">
                  <option>가격</option>
                  <option>~ ₩30,000</option>
                  <option>₩30,000+</option>
                </select>
              </div>
              <div className="relative">
                <textarea
                  value={vibeInput}
                  onChange={(e) => setVibeInput(e.target.value)}
                  onFocus={() => setFocused(true)}
                  onBlur={() => setTimeout(() => setFocused(false), 140)}
                  placeholder="비오는 날 조용히 책 읽기 좋은..."
                  className="h-36 w-full rounded-2xl border border-amber-200/80 bg-white/70 p-4 outline-none focus:ring-2 focus:ring-amber-300"
                />
                <AnimatePresence>
                  {focused && (
                    <motion.div
                      initial={{ opacity: 0, y: -8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -8 }}
                      className="glass absolute left-0 top-full z-10 mt-2 w-full rounded-2xl p-4"
                    >
                      <p className="mb-2 text-xs uppercase tracking-wide text-stone-500">지금 뜨는 무드</p>
                      <div className="mb-4 flex flex-wrap gap-2">
                        {recommendedVibes.slice(0, 3).map((v) => (
                          <button
                            key={v}
                            onClick={() => setVibeInput(v)}
                            className="rounded-full bg-orange-100 px-3 py-1.5 text-sm"
                          >
                            {v}
                          </button>
                        ))}
                      </div>
                      <p className="mb-2 text-xs uppercase tracking-wide text-stone-500">
                        내 최근 취향 기반 추천
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {recommendedVibes.slice(3).map((v) => (
                          <button
                            key={v}
                            onClick={() => setVibeInput(v)}
                            className="rounded-full bg-amber-100 px-3 py-1.5 text-sm"
                          >
                            {v}
                          </button>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
              <button
                onClick={runSearch}
                className="mt-4 inline-flex items-center gap-2 rounded-xl bg-amber-500 px-4 py-2 font-medium text-white hover:bg-amber-400"
              >
                <Search className="h-4 w-4" /> 검색
              </button>
            </div>

            <div>
              {loading ? (
                <div className="glass rounded-2xl p-10 text-center">
                  <LoaderCircle className="mx-auto h-8 w-8 animate-spin text-amber-500" />
                  <p className="mt-3">AI 벡터 연산 중...</p>
                </div>
              ) : searched.length > 0 ? (
                <MasonryCards source={searched} />
              ) : (
                <p className="text-stone-500">검색 결과가 여기에 Masonry Grid로 표시됩니다.</p>
              )}
            </div>
          </section>
        )}
      </div>

      <AnimatePresence>
        {selected && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 grid place-items-center bg-stone-900/40 p-4"
            onClick={() => setSelected(null)}
          >
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: 20, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="glass max-h-[90vh] w-full max-w-2xl overflow-auto rounded-3xl"
            >
              <img src={selected.image} alt={selected.title} className="h-72 w-full object-cover" />
              <div className="p-6">
                <h3 className="text-2xl font-bold">{selected.title}</h3>
                <div className="mt-4 flex flex-wrap gap-2 text-sm">
                  <span className="inline-flex items-center gap-1 rounded-full bg-amber-100/80 px-3 py-1">
                    <Tag className="h-3.5 w-3.5" /> {selected.category}
                  </span>
                  {selected.price && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-amber-100/80 px-3 py-1">
                      <BadgeDollarSign className="h-3.5 w-3.5" /> {selected.price}
                    </span>
                  )}
                  {selected.location && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-amber-100/80 px-3 py-1">
                      <MapPin className="h-3.5 w-3.5" /> {selected.location}
                    </span>
                  )}
                  <span className="inline-flex items-center gap-1 rounded-full bg-amber-100/80 px-3 py-1">
                    <CalendarClock className="h-3.5 w-3.5" /> 최근 스크랩
                  </span>
                </div>
                <div className="mt-6 rounded-2xl bg-amber-50/70 p-4">
                  <p className="text-sm uppercase tracking-wide text-stone-500">관련 외부 정보</p>
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-stone-700">
                    <li>네이버 리뷰 평점 4.7 / 5.0</li>
                    <li>인스타그램 최근 언급량 지난주 대비 +28%</li>
                    <li>블로그 요약: "조용하고 책 읽기 좋은 좌석"</li>
                  </ul>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showLoginModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[70] grid place-items-center bg-stone-900/45 p-4"
            onClick={() => !loginLoading && setShowLoginModal(false)}
          >
            <motion.div
              initial={{ y: 16, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: 16, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="glass w-full max-w-md rounded-3xl p-6"
            >
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-bold">Instagram 계정 연결</h3>
                <button
                  onClick={() => !loginLoading && setShowLoginModal(false)}
                  className="rounded-full p-1 text-stone-600 hover:bg-amber-100/70"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
              <p className="mb-5 text-sm text-stone-600">
                스크랩 데이터를 동기화해 Fact/Vibe 벡터를 업데이트하려면 인스타그램 로그인이 필요합니다.
              </p>
              <button
                onClick={runInstagramLogin}
                disabled={loginLoading}
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-amber-500 to-orange-400 px-4 py-3 font-semibold text-white disabled:opacity-70 shadow-[0_12px_30px_rgba(221,146,72,0.32)]"
              >
                {loginLoading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Instagram className="h-4 w-4" />}
                {loginLoading ? 'Instagram OAuth 연결 중...' : '인스타그램으로 로그인'}
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}
