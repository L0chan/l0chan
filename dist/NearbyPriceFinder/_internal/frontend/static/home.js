const { useEffect, useMemo, useRef, useState } = React;

        const account = window.NPF_ACCOUNT || { role: "customer", user: "Guest", isOwnerAdmin: false };

        const navLinks = [
            { label: "Customer", href: "/customer" },
            { label: "Shopkeeper", href: "/shopkeeper" },
            { label: "Dashboard", href: "/shopkeeper_dashboard" },
            { label: "Analytics", href: "/dashboard" },
            { label: "Owner Panel", href: "/admin", roles: ["admin"] },
            { label: "Live Chat", href: "/live_chat" },
            { label: "Logout", href: "/logout" },
        ].filter((link) => !link.roles || link.roles.includes(account.role));

        const features = [
            {
                id: "search",
                icon: "S",
                title: "Smart Nearby Search",
                text: "Find products near your location instantly using maps.",
                accent: "#21d4fd",
            },
            {
                id: "tracking",
                icon: "T",
                title: "Live Order Tracking",
                text: "Real-time order updates from preparation to delivery.",
                accent: "#37e07f",
            },
            {
                id: "payment",
                icon: "P",
                title: "Secure Payment",
                text: "COD, UPI QR payments and delivery address support.",
                accent: "#ffb84c",
            },
        ];

        const quickCards = [
            { value: "2 min", text: "Average product discovery flow from search to shop." },
            { value: "Local", text: "Built for nearby stores, fresh stock, and quick pickup." },
            { value: "Simple", text: "Clear customer, seller, payment, and tracking journeys." },
        ];

        const heroLottieData = {
            v: "5.7.4",
            fr: 30,
            ip: 0,
            op: 120,
            w: 420,
            h: 280,
            nm: "Nearby shopping motion",
            ddd: 0,
            assets: [],
            layers: [
                {
                    ddd: 0,
                    ind: 1,
                    ty: 4,
                    nm: "route",
                    sr: 1,
                    ks: {
                        o: { a: 0, k: 100 },
                        r: { a: 0, k: 0 },
                        p: { a: 0, k: [210, 145, 0] },
                        a: { a: 0, k: [0, 0, 0] },
                        s: { a: 0, k: [100, 100, 100] },
                    },
                    shapes: [
                        {
                            ty: "sh",
                            ks: {
                                a: 0,
                                k: {
                                    i: [[-36, -40], [-34, 45], [-24, -18], [0, 0]],
                                    o: [[42, 47], [30, -40], [24, 18], [0, 0]],
                                    v: [[-150, 50], [-30, -56], [82, 34], [156, -32]],
                                    c: false,
                                },
                            },
                        },
                        {
                            ty: "st",
                            c: { a: 0, k: [0.129, 0.831, 0.992, 1] },
                            o: { a: 0, k: 100 },
                            w: { a: 0, k: 8 },
                            lc: 2,
                            lj: 2,
                        },
                        {
                            ty: "tm",
                            s: { a: 0, k: 0 },
                            e: {
                                a: 1,
                                k: [
                                    { t: 0, s: [12], e: [100] },
                                    { t: 54, s: [100], e: [100] },
                                    { t: 120, s: [100] },
                                ],
                            },
                            o: { a: 0, k: 0 },
                        },
                    ],
                    ip: 0,
                    op: 120,
                    st: 0,
                    bm: 0,
                },
                {
                    ddd: 0,
                    ind: 2,
                    ty: 4,
                    nm: "shopping marker",
                    sr: 1,
                    ks: {
                        o: { a: 0, k: 100 },
                        r: {
                            a: 1,
                            k: [
                                { t: 0, s: [-8], e: [8] },
                                { t: 60, s: [8], e: [-8] },
                                { t: 120, s: [-8] },
                            ],
                        },
                        p: {
                            a: 1,
                            k: [
                                { t: 0, s: [60, 190, 0], e: [180, 92, 0] },
                                { t: 60, s: [180, 92, 0], e: [330, 112, 0] },
                                { t: 120, s: [330, 112, 0] },
                            ],
                        },
                        a: { a: 0, k: [0, 0, 0] },
                        s: {
                            a: 1,
                            k: [
                                { t: 0, s: [92, 92, 100], e: [108, 108, 100] },
                                { t: 60, s: [108, 108, 100], e: [92, 92, 100] },
                                { t: 120, s: [92, 92, 100] },
                            ],
                        },
                    },
                    shapes: [
                        {
                            ty: "el",
                            p: { a: 0, k: [0, 0] },
                            s: { a: 0, k: [78, 78] },
                        },
                        {
                            ty: "fl",
                            c: { a: 0, k: [1, 0.722, 0.298, 1] },
                            o: { a: 0, k: 100 },
                        },
                        {
                            ty: "el",
                            p: { a: 0, k: [0, 0] },
                            s: { a: 0, k: [28, 28] },
                        },
                        {
                            ty: "fl",
                            c: { a: 0, k: [0.024, 0.067, 0.122, 1] },
                            o: { a: 0, k: 100 },
                        },
                    ],
                    ip: 0,
                    op: 120,
                    st: 0,
                    bm: 0,
                },
                {
                    ddd: 0,
                    ind: 3,
                    ty: 4,
                    nm: "pulse",
                    sr: 1,
                    ks: {
                        o: {
                            a: 1,
                            k: [
                                { t: 0, s: [55], e: [0] },
                                { t: 80, s: [0], e: [55] },
                                { t: 120, s: [55] },
                            ],
                        },
                        r: { a: 0, k: 0 },
                        p: { a: 0, k: [210, 145, 0] },
                        a: { a: 0, k: [0, 0, 0] },
                        s: {
                            a: 1,
                            k: [
                                { t: 0, s: [70, 70, 100], e: [135, 135, 100] },
                                { t: 80, s: [135, 135, 100], e: [70, 70, 100] },
                                { t: 120, s: [70, 70, 100] },
                            ],
                        },
                    },
                    shapes: [
                        {
                            ty: "el",
                            p: { a: 0, k: [0, 0] },
                            s: { a: 0, k: [170, 170] },
                        },
                        {
                            ty: "st",
                            c: { a: 0, k: [0.231, 0.878, 0.498, 1] },
                            o: { a: 0, k: 100 },
                            w: { a: 0, k: 5 },
                        },
                    ],
                    ip: 0,
                    op: 120,
                    st: 0,
                    bm: 0,
                },
            ],
        };

        function useLottie(containerRef, animationData) {
            useEffect(() => {
                if (!containerRef.current || !window.lottie) return undefined;

                let animation;

                try {
                    animation = window.lottie.loadAnimation({
                        container: containerRef.current,
                        renderer: "svg",
                        loop: true,
                        autoplay: true,
                        animationData,
                    });
                } catch (error) {
                    console.warn("Lottie animation could not be loaded.", error);
                }

                return () => {
                    if (animation) animation.destroy();
                };
            }, [containerRef, animationData]);
        }

        function BackgroundFlow() {
            const items = useMemo(() => (
                Array.from({ length: 11 }, (_, index) => ({
                    id: index,
                    left: `${8 + index * 8}%`,
                    size: `${70 + (index % 4) * 34}px`,
                    duration: `${17 + (index % 5) * 3}s`,
                    delay: `${index * -1.7}s`,
                }))
            ), []);

            return (
                <div className="background-flow" aria-hidden="true">
                    {items.map((item) => (
                        <span
                            className="orb"
                            key={item.id}
                            style={{
                                "--left": item.left,
                                "--size": item.size,
                                "--duration": item.duration,
                                "--delay": item.delay,
                            }}
                        />
                    ))}
                </div>
            );
        }

        function Navbar() {
            return (
                <nav className="navbar">
                    <a className="brand" href="/home" aria-label="Nearby Price Finder home">
                        <span className="brand-mark">NP</span>
                        <span className="brand-text">Nearby Price Finder</span>
                    </a>
                    <div className="nav-links">
                        <span className="account-chip">{account.role}: {account.user}</span>
                        {navLinks.map((link) => (
                            <a key={link.href} href={link.href}>{link.label}</a>
                        ))}
                    </div>
                </nav>
            );
        }

        function HeroLottie() {
            const ref = useRef(null);
            useLottie(ref, heroLottieData);
            return <div className="lottie-stage" ref={ref} aria-hidden="true" />;
        }

        function PlatformCard({ onFeatureClick }) {
            return (
                <div className="glass-card">
                    <div className="card-top">
                        <h2>Live Platform</h2>
                        <span className="status"><span className="pulse-dot" /> Active</span>
                    </div>

                    {features.map((feature) => (
                        <button
                            className="feature"
                            key={feature.id}
                            type="button"
                            onClick={() => onFeatureClick(feature.id)}
                        >
                            <h3>
                                <span className="feature-icon" style={{ "--accent": feature.accent }}>
                                    {feature.icon}
                                </span>
                                {feature.title}
                            </h3>
                            <p>{feature.text}</p>
                        </button>
                    ))}

                    <div className="stats">
                        <div className="stat-box">
                            <div>
                                <h3>500+</h3>
                                <p>Products</p>
                            </div>
                        </div>
                        <div className="stat-box">
                            <div>
                                <h3>120+</h3>
                                <p>Shops</p>
                            </div>
                        </div>
                        <div className="stat-box">
                            <div>
                                <h3>24/7</h3>
                                <p>Tracking</p>
                            </div>
                        </div>
                    </div>
                </div>
            );
        }

        function SearchModalContent() {
            const [query, setQuery] = useState("");
            const normalized = query.trim().toLowerCase();
            const result = useMemo(() => {
                if (!normalized) return null;

                if (normalized === "rice") {
                    return {
                        title: "Rice available nearby",
                        lines: ["Fresh Mart - Rs. 50 - 1 KM", "Super Shop - Rs. 55 - 2 KM"],
                    };
                }

                if (normalized === "milk") {
                    return {
                        title: "Milk available nearby",
                        lines: ["Dairy Fresh - Rs. 30 - 500 m"],
                    };
                }

                return {
                    title: "Product not found nearby",
                    lines: ["Try rice or milk in this demo search."],
                };
            }, [normalized]);

            return (
                <>
                    <input
                        className="modal-input"
                        value={query}
                        onChange={(event) => setQuery(event.target.value)}
                        placeholder="Search product"
                        autoFocus
                    />
                    {result && (
                        <div className="result-card">
                            <strong>{result.title}</strong>
                            {result.lines.map((line) => (
                                <div key={line}>{line}</div>
                            ))}
                        </div>
                    )}
                </>
            );
        }

        function TrackingModalContent() {
            const steps = [
                "Order confirmed",
                "Preparing product",
                "Out for delivery",
                "Arriving soon",
            ];

            return (
                <div>
                    {steps.map((step) => (
                        <div className="timeline-item" key={step}>
                            <span className="timeline-dot" />
                            <strong>{step}</strong>
                        </div>
                    ))}
                </div>
            );
        }

        function PaymentModalContent() {
            return (
                <>
                    <div className="payment-grid">
                        <div className="payment-option">
                            <strong>Cash On Delivery</strong>
                            <div>Pay when your order reaches you.</div>
                        </div>
                        <div className="payment-option">
                            <strong>UPI QR Payment</strong>
                            <div>Scan and pay quickly from any UPI app.</div>
                        </div>
                    </div>
                    <input className="modal-input" placeholder="Enter delivery address" />
                </>
            );
        }

        function FeatureModal({ activeModal, onClose }) {
            if (!activeModal) return null;

            const modalMap = {
                search: {
                    title: "Nearby Product Search",
                    content: <SearchModalContent />,
                },
                tracking: {
                    title: "Live Tracking",
                    content: <TrackingModalContent />,
                },
                payment: {
                    title: "Payment System",
                    content: <PaymentModalContent />,
                },
            };

            const modal = modalMap[activeModal];

            return (
                <div className="modal-backdrop" role="dialog" aria-modal="true" onClick={onClose}>
                    <section className="modal" onClick={(event) => event.stopPropagation()}>
                        <div className="modal-header">
                            <h2>{modal.title}</h2>
                            <button className="close-btn" type="button" onClick={onClose} aria-label="Close modal">
                                x
                            </button>
                        </div>
                        {modal.content}
                    </section>
                </div>
            );
        }

        function AiAssistant() {
            const [isOpen, setIsOpen] = useState(false);
            const [input, setInput] = useState("");
            const [isSending, setIsSending] = useState(false);
            const [messages, setMessages] = useState([
                {
                    from: "bot",
                    text: "Hi, I am your shopping assistant. Ask me to find a product, compare prices, or explain tracking.",
                },
            ]);
            const messagesRef = useRef(null);

            const starterPrompts = [
                "Find laptop nearby",
                "Show cheapest bag",
                "How can I track my order?",
            ];

            useEffect(() => {
                if (messagesRef.current) {
                    messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
                }
            }, [messages, isSending, isOpen]);

            const sendMessage = async (messageText = input) => {
                const cleanMessage = messageText.trim();
                if (!cleanMessage || isSending) return;

                setInput("");
                setIsOpen(true);
                setIsSending(true);
                setMessages((current) => [
                    ...current,
                    { from: "user", text: cleanMessage },
                ]);

                try {
                    const response = await fetch("/chat_response", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/x-www-form-urlencoded",
                        },
                        body: new URLSearchParams({ message: cleanMessage }),
                    });

                    if (!response.ok) {
                        throw new Error("Chat request failed");
                    }

                    const data = await response.json();
                    setMessages((current) => [
                        ...current,
                        { from: "bot", text: data.reply || "I am ready to help. Try a product name." },
                    ]);
                } catch (error) {
                    setMessages((current) => [
                        ...current,
                        { from: "bot", text: "I could not connect right now. Please try again in a moment." },
                    ]);
                } finally {
                    setIsSending(false);
                }
            };

            const handleSubmit = (event) => {
                event.preventDefault();
                sendMessage();
            };

            return (
                <section className={`assistant-widget ${isOpen ? "open" : ""}`} aria-label="AI shopping assistant">
                    {isOpen && (
                        <div className="assistant-panel">
                            <div className="assistant-header">
                                <div>
                                    <span>AI Shopping Assistant</span>
                                    <strong>Ready to help</strong>
                                </div>
                                <button
                                    className="assistant-icon-btn"
                                    type="button"
                                    onClick={() => setIsOpen(false)}
                                    aria-label="Close AI assistant"
                                >
                                    x
                                </button>
                            </div>

                            <div className="assistant-messages" ref={messagesRef}>
                                {messages.map((message, index) => (
                                    <div className={`assistant-message ${message.from}`} key={`${message.from}-${index}`}>
                                        {message.text}
                                    </div>
                                ))}
                                {isSending && (
                                    <div className="assistant-message bot">
                                        Checking nearby options...
                                    </div>
                                )}
                            </div>

                            <div className="assistant-prompts" aria-label="Quick assistant prompts">
                                {starterPrompts.map((prompt) => (
                                    <button
                                        type="button"
                                        key={prompt}
                                        onClick={() => sendMessage(prompt)}
                                        disabled={isSending}
                                    >
                                        {prompt}
                                    </button>
                                ))}
                            </div>

                            <form className="assistant-form" onSubmit={handleSubmit}>
                                <input
                                    value={input}
                                    onChange={(event) => setInput(event.target.value)}
                                    placeholder="Ask about products, prices, or orders"
                                    aria-label="Message AI shopping assistant"
                                />
                                <button type="submit" disabled={isSending || !input.trim()}>
                                    Send
                                </button>
                            </form>
                        </div>
                    )}

                    <button
                        className="assistant-toggle"
                        type="button"
                        onClick={() => setIsOpen((current) => !current)}
                        aria-expanded={isOpen}
                        aria-label={isOpen ? "Close AI assistant" : "Open AI assistant"}
                    >
                        AI
                    </button>
                </section>
            );
        }

        function App() {
            const [activeModal, setActiveModal] = useState(null);
            return (
                <>
                    <BackgroundFlow />
                    <main className="page-shell">
                        <Navbar />
                        <section className="hero">
                            <div className="hero-copy">
                                <div className="eyebrow">
                                    <span className="pulse-dot" />
                                    Smart Nearby Shopping Platform
                                </div>
                                <h1>
                                    Find nearby <span>products</span> faster than ever.
                                </h1>
                                <p>
                                    Discover nearby shops, compare prices, track live orders, use OTP login,
                                    manage delivery status, and shop with a polished local marketplace experience.
                                </p>
                                <div className="actions">
                                    <a className="btn primary" href="/customer">Explore Products</a>
                                    <a className="btn secondary" href="/shopkeeper">Upload Products</a>
                                </div>
                            </div>

                            <div className="hero-visual">
                                <HeroLottie />
                                <PlatformCard onFeatureClick={setActiveModal} />
                            </div>
                        </section>

                        <section className="quick-strip" aria-label="Platform highlights">
                            {quickCards.map((card) => (
                                <article className="quick-card" key={card.value}>
                                    <strong>{card.value}</strong>
                                    <span>{card.text}</span>
                                </article>
                            ))}
                        </section>
                    </main>
                    <FeatureModal activeModal={activeModal} onClose={() => setActiveModal(null)} />
                    <AiAssistant />
                </>
            );
        }

        ReactDOM.createRoot(document.getElementById("root")).render(<App />);

