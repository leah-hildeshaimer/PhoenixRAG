export default function PhoenixBackground() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 z-0 overflow-hidden"
    >
      {/* Base background */}
      <div
        className="absolute inset-0"
        style={{
          background: `
            radial-gradient(ellipse at 10% 88%, rgba(255, 171, 121, 0.17), transparent 52%),
            radial-gradient(ellipse at 92% 8%, rgba(125, 171, 235, 0.15), transparent 48%),
            linear-gradient(135deg, #F8FBFF 0%, #FFFFFF 52%, #FFF8F3 100%)
          `,
        }}
      />

      {/* Phoenix-inspired flowing wings */}
      <svg
        className="absolute bottom-0 left-0 h-full w-[min(78%,1100px)]"
        viewBox="0 0 1100 900"
        preserveAspectRatio="xMinYMax meet"
        fill="none"
      >
        <defs>
          <linearGradient id="wingA" x1="0" y1="0" x2="900" y2="800">
            <stop offset="0%" stopColor="#FF7A36" stopOpacity="0.18" />
            <stop offset="100%" stopColor="#FFD9C4" stopOpacity="0.035" />
          </linearGradient>
          <linearGradient id="wingB" x1="50" y1="200" x2="800" y2="850">
            <stop offset="0%" stopColor="#FF9B61" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#FFE3D1" stopOpacity="0.025" />
          </linearGradient>
        </defs>

        <path
          d="M -160 90 C 30 110 205 180 310 325 C 390 435 435 565 550 665 C 655 760 820 805 1060 825 C 805 858 565 805 390 700 C 235 605 175 435 85 310 C 5 205 -95 150 -160 155 Z"
          fill="url(#wingA)"
        />
        <path
          d="M -145 245 C 35 265 165 360 235 495 C 300 625 405 730 600 820 C 395 775 255 680 155 545 C 65 415 -30 345 -145 330 Z"
          fill="url(#wingB)"
        />
        <path
          d="M 5 365 C 175 390 270 500 340 615 C 425 745 575 810 805 860 C 555 855 365 790 240 665 C 140 565 80 450 5 365 Z"
          fill="#FFAD7E"
          fillOpacity="0.085"
        />
        <path
          d="M -145 585 C 60 625 190 710 340 785 C 535 875 790 880 1110 850 C 825 940 490 955 225 870 C 40 810 -65 720 -145 705 Z"
          fill="#FF9A61"
          fillOpacity="0.075"
        />
        <path
          d="M 105 445 C 130 320 215 225 350 190 C 270 280 245 390 255 515 C 220 470 175 450 105 445 Z"
          fill="#FF8D50"
          fillOpacity="0.075"
        />
      </svg>

      {/* Subtle ambient glow */}
      <div className="absolute -right-48 -top-52 h-[650px] w-[650px] rounded-full bg-blue-100/25 blur-[110px]" />
    </div>
  );
}