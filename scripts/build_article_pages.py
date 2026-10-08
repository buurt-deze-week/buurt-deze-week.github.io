#!/usr/bin/env python3
import copy
import datetime as dt
import html
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "editie.json"
OUTPUT_FILE = ROOT / "editie-site.json"
ARTICLES_DIR = ROOT / "berichten"
IMAGES_DIR = ROOT / "assets" / "berichten"
SITE_URL = "https://www.buurtdezeweek.nl"
DETAIL_CSS = '\n    :root {\n      --bg:#fbfaf6;\n      --paper:#fffdf9;\n      --ink:#121914;\n      --body:#4a544f;\n      --muted:#717973;\n      --line:#d8d4c8;\n      --blue:#155eef;\n      --blue-dark:#0c438f;\n      --green:#226649;\n      --orange:#af5d27;\n      --soft-blue:#eef3ff;\n      --soft-green:#edf6f0;\n      --soft-orange:#fff1e6;\n      --ornament:#e7d8b5;\n      --ornament-2:#c2d6c7;\n      --serif:Georgia,"Times New Roman",serif;\n      --sans:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;\n      --max:980px;\n    }\n\n    * { box-sizing:border-box; }\n    html { scroll-behavior:smooth; }\n    body {\n      margin:0;\n      font-family:var(--sans);\n      color:var(--ink);\n      background:var(--bg);\n      line-height:1.45;\n      -webkit-font-smoothing:antialiased;\n      overflow-x:hidden;\n      position:relative;\n    }\n    a { color:inherit; }\n    img { display:block; max-width:100%; }\n    button,input,textarea { font:inherit; }\n    .wrap { width:min(calc(100% - 32px),var(--max)); margin:0 auto; position:relative; z-index:2; }\n\n    .page-ornaments {\n      position:fixed;\n      inset:0;\n      pointer-events:none;\n      overflow:hidden;\n      z-index:0;\n    }\n    .ornament {\n      position:absolute;\n      opacity:.6;\n      filter:blur(.0px);\n    }\n    .ornament svg { display:block; }\n    .ornament.top-right { top:86px; right:22px; }\n    .ornament.mid-left { top:560px; left:16px; }\n    .ornament.bottom-right { right:28px; bottom:130px; }\n    .ornament.badge-053 {\n      top:182px;\n      right:110px;\n      padding:8px 12px;\n      border:1px solid rgba(22,94,239,.18);\n      border-radius:999px;\n      background:rgba(255,253,249,.78);\n      color:#7d866f;\n      font-size:.75rem;\n      font-weight:800;\n      letter-spacing:.16em;\n    }\n    .ornament.badge-textiel {\n      left:48px;\n      bottom:250px;\n      padding:8px 12px;\n      border-radius:999px;\n      background:rgba(255,253,249,.72);\n      border:1px solid rgba(194,214,199,.45);\n      color:#7a827c;\n      font-size:.72rem;\n      font-weight:800;\n      letter-spacing:.08em;\n    }\n\n    .sitebar {\n      position:sticky;\n      top:0;\n      z-index:30;\n      border-bottom:1px solid rgba(80,79,70,.10);\n      background:rgba(251,250,246,.96);\n      backdrop-filter:blur(12px);\n    }\n    .sitebar-inner {\n      min-height:64px;\n      display:flex;\n      align-items:center;\n      justify-content:space-between;\n      gap:22px;\n    }\n    .brandline {\n      display:flex;\n      align-items:center;\n      gap:12px;\n      min-width:0;\n    }\n    .brandlink {\n      text-decoration:none;\n      font-family:var(--serif);\n      font-size:1.55rem;\n      font-weight:700;\n      letter-spacing:-.035em;\n      white-space:nowrap;\n    }\n    .brandlink .dot { color:var(--blue); }\n    .location {\n      display:inline-flex;\n      align-items:center;\n      gap:6px;\n      color:#48524c;\n      font-size:.82rem;\n      font-weight:700;\n      white-space:nowrap;\n    }\n    .location svg { width:15px; height:15px; color:var(--blue); }\n    .nav {\n      display:flex;\n      align-items:center;\n      gap:21px;\n      font-size:.82rem;\n      font-weight:760;\n    }\n    .nav a {\n      text-decoration:none;\n    }\n    .nav a:hover { color:var(--blue-dark); }\n    .nav .inbox {\n      border:1px solid #b5c5e8;\n      border-radius:999px;\n      padding:9px 13px;\n      color:var(--blue-dark);\n    }\n\n    .hero {\n      padding:46px 0 28px;\n      border-bottom:1px solid rgba(80,79,70,.12);\n      position:relative;\n    }\n    .hero-grid {\n      display:grid;\n      grid-template-columns:minmax(0,1.08fr) minmax(320px,.92fr);\n      gap:42px;\n      align-items:center;\n    }\n    .edition-date {\n      color:#345247;\n      font-size:.84rem;\n      margin-bottom:9px;\n    }\n    .edition-brand {\n      color:var(--blue-dark);\n      font-size:.8rem;\n      font-weight:850;\n      margin-bottom:7px;\n    }\n    .edition-title {\n      margin:0;\n      max-width:650px;\n      font-family:var(--serif);\n      font-size:clamp(3rem,6vw,4.8rem);\n      line-height:.92;\n      letter-spacing:-.052em;\n      font-weight:700;\n    }\n    .edition-title .dot { color:var(--blue); }\n    .edition-intro {\n      margin:20px 0 0;\n      max-width:650px;\n      color:#3f4943;\n      font-size:1.08rem;\n      line-height:1.55;\n    }\n    .hero-meta {\n      display:flex;\n      flex-wrap:wrap;\n      gap:8px 0;\n      margin-top:22px;\n      padding-top:14px;\n      border-top:1px solid #bfc5bd;\n      color:#707873;\n      font-size:.78rem;\n    }\n    .hero-meta span {\n      display:inline-flex;\n      align-items:center;\n    }\n    .hero-meta span:not(:last-child)::after {\n      content:"·";\n      margin:0 10px;\n      color:#989e99;\n    }\n    .hero-visual {\n      position:relative;\n      min-height:285px;\n      border-radius:0 0 0 78px;\n      overflow:hidden;\n      background:#ebe7dc;\n      box-shadow:0 18px 40px rgba(50,55,48,.05);\n    }\n    .hero-visual img {\n      width:100%;\n      height:100%;\n      min-height:285px;\n      object-fit:cover;\n    }\n    .hero-visual:after {\n      content:"";\n      position:absolute;\n      inset:0;\n      background:linear-gradient(90deg,rgba(251,250,246,.32) 0%,rgba(251,250,246,0) 38%);\n      pointer-events:none;\n    }\n\n    .feed-shell { padding:34px 0 10px; }\n    .feed-head {\n      display:flex;\n      align-items:flex-end;\n      justify-content:space-between;\n      gap:20px;\n      padding-bottom:10px;\n      border-bottom:1px solid #9ba69f;\n    }\n    .feed-title {\n      margin:0;\n      color:var(--green);\n      font-size:.78rem;\n      text-transform:uppercase;\n      letter-spacing:.13em;\n      font-weight:900;\n    }\n    .feed-count {\n      color:var(--muted);\n      font-size:.78rem;\n      white-space:nowrap;\n    }\n    .feed-title::after {\n      content:"";\n      display:block;\n      width:34px;\n      height:2px;\n      background:#d6a347;\n      margin-top:10px;\n    }\n\n    .filters {\n      display:flex;\n      gap:6px;\n      overflow:auto;\n      padding:12px 0 2px;\n      scrollbar-width:none;\n    }\n    .filters::-webkit-scrollbar { display:none; }\n    .filter {\n      border:0;\n      background:transparent;\n      color:#6f7772;\n      padding:6px 0;\n      margin-right:16px;\n      font-size:.78rem;\n      font-weight:800;\n      cursor:pointer;\n      white-space:nowrap;\n      border-bottom:2px solid transparent;\n    }\n    .filter:hover { color:var(--blue-dark); }\n    .filter.active {\n      color:var(--blue-dark);\n      border-bottom-color:var(--blue);\n    }\n\n    .stories { margin-top:4px; }\n    .story {\n      border-bottom:1px solid var(--line);\n      position:relative;\n    }\n    .story-link {\n      display:grid;\n      grid-template-columns:18px minmax(0,1fr) 168px;\n      gap:16px;\n      align-items:center;\n      padding:18px 0;\n      text-decoration:none;\n    }\n    .story-link:hover .story-title { color:var(--blue-dark); }\n    .story-bullet {\n      width:4px;\n      height:4px;\n      border-radius:50%;\n      background:#d6b36b;\n      margin-top:10px;\n      align-self:start;\n    }\n    .story-main { min-width:0; }\n    .story-category {\n      color:var(--blue);\n      text-transform:uppercase;\n      font-size:.68rem;\n      letter-spacing:.12em;\n      font-weight:900;\n      margin-bottom:4px;\n    }\n    .story-title {\n      margin:0;\n      font-family:var(--serif);\n      font-size:1.55rem;\n      line-height:1.08;\n      letter-spacing:-.03em;\n      transition:color .15s ease;\n    }\n    .story-summary {\n      margin:7px 0 0;\n      color:#59625d;\n      font-size:.9rem;\n      line-height:1.42;\n      max-width:96%;\n      display:-webkit-box;\n      -webkit-line-clamp:2;\n      -webkit-box-orient:vertical;\n      overflow:hidden;\n    }\n    .story-meta {\n      display:flex;\n      flex-wrap:wrap;\n      gap:8px;\n      margin-top:9px;\n      color:#6a756f;\n      font-size:.72rem;\n      font-weight:780;\n      align-items:center;\n    }\n    .story-tag {\n      display:inline-flex;\n      align-items:center;\n      padding:6px 10px;\n      border-radius:999px;\n      background:var(--soft-blue);\n      color:#4b6899;\n      font-size:.68rem;\n      letter-spacing:.03em;\n      font-weight:900;\n    }\n    .story-tag.green {\n      background:var(--soft-green);\n      color:#397053;\n    }\n    .story-tag.orange {\n      background:var(--soft-orange);\n      color:#9c602e;\n    }\n    .story-thumb,\n    .story-thumb-placeholder {\n      width:168px;\n      height:116px;\n      border-radius:11px;\n      overflow:hidden;\n      background:#ebe6db;\n      justify-self:end;\n    }\n    .story-thumb {\n      object-fit:cover;\n      box-shadow:0 8px 22px rgba(60,64,58,.05);\n    }\n    .story-thumb-placeholder {\n      display:grid;\n      place-items:center;\n      text-align:center;\n      padding:14px;\n      color:#8b908b;\n      font-family:var(--serif);\n      font-size:.8rem;\n      background:linear-gradient(145deg,#e8e2d6,#f8f5ee);\n    }\n    .edition-loading,.edition-error {\n      padding:30px 0;\n      color:var(--muted);\n      font-size:.92rem;\n    }\n\n    .signup {\n      margin:42px 0 18px;\n      border-top:1px solid var(--line);\n      border-bottom:1px solid var(--line);\n      padding:24px 0;\n      display:grid;\n      grid-template-columns:minmax(0,1fr) minmax(280px,.85fr);\n      gap:28px;\n      align-items:center;\n    }\n    .signup h2 {\n      margin:0 0 4px;\n      font-family:var(--serif);\n      font-size:1.5rem;\n      letter-spacing:-.025em;\n    }\n    .signup p {\n      margin:0;\n      color:#626a65;\n      font-size:.85rem;\n    }\n    .signup-form {\n      display:flex;\n      gap:8px;\n    }\n    .signup-form input {\n      min-width:0;\n      flex:1;\n      border:1px solid #d3d0c7;\n      background:var(--paper);\n      padding:11px 12px;\n      border-radius:10px;\n      color:var(--ink);\n    }\n    .button {\n      border:0;\n      border-radius:10px;\n      background:var(--blue);\n      color:#fff;\n      padding:11px 15px;\n      font-weight:850;\n      cursor:pointer;\n      text-decoration:none;\n      display:inline-flex;\n      align-items:center;\n      justify-content:center;\n      white-space:nowrap;\n    }\n    .button:hover { background:#0c50d7; }\n    .signup-confirm {\n      grid-column:2;\n      margin-top:-18px;\n      color:#8a918c;\n      font-size:.7rem;\n    }\n\n    .tipbox {\n      margin:24px 0 8px;\n      padding:21px 0;\n      display:grid;\n      grid-template-columns:minmax(0,1fr) auto;\n      gap:20px;\n      align-items:center;\n      border-bottom:1px solid var(--line);\n    }\n    .tipbox h2 {\n      margin:0 0 4px;\n      font-family:var(--serif);\n      font-size:1.34rem;\n      letter-spacing:-.02em;\n    }\n    .tipbox > div > p {\n      margin:0;\n      color:#657069;\n      font-size:.84rem;\n    }\n    .tip-details summary {\n      list-style:none;\n      cursor:pointer;\n      border:1px solid #c7c9c2;\n      border-radius:999px;\n      padding:9px 14px;\n      font-size:.8rem;\n      font-weight:850;\n      white-space:nowrap;\n    }\n    .tip-details summary::-webkit-details-marker { display:none; }\n    .tip-details[open] {\n      grid-column:1/-1;\n      width:100%;\n    }\n    .tip-details[open] summary {\n      display:inline-block;\n      margin-bottom:16px;\n    }\n    .tip-form {\n      display:grid;\n      gap:9px;\n      max-width:650px;\n      padding-top:18px;\n      border-top:1px solid var(--line);\n    }\n    .tip-form label {\n      color:#405048;\n      font-size:.76rem;\n      font-weight:850;\n    }\n    .tip-form input,.tip-form textarea {\n      width:100%;\n      border:1px solid #d1cec4;\n      background:var(--paper);\n      color:var(--ink);\n      border-radius:10px;\n      padding:11px 12px;\n    }\n    .tip-form textarea { min-height:115px; resize:vertical; }\n    .tip-note,.tip-error {\n      margin:0;\n      color:var(--muted);\n      font-size:.74rem;\n    }\n    .tip-error { color:#9d3c31; }\n\n    .info {\n      padding:18px 0 0;\n      color:var(--muted);\n      font-size:.79rem;\n    }\n    .info details {\n      border-bottom:1px solid var(--line);\n      padding:10px 0;\n    }\n    .info summary {\n      cursor:pointer;\n      list-style:none;\n      font-weight:850;\n      color:#323b36;\n    }\n    .info summary::-webkit-details-marker { display:none; }\n    .info p { max-width:690px; margin:8px 0 3px; }\n    .info a { color:var(--blue-dark); font-weight:750; }\n    .contact-line {\n      display:flex;\n      align-items:center;\n      flex-wrap:wrap;\n      gap:8px;\n      margin-top:7px;\n    }\n    .copy-email {\n      border:1px solid #d1cec4;\n      border-radius:8px;\n      background:var(--paper);\n      padding:6px 9px;\n      cursor:pointer;\n      font-size:.72rem;\n      font-weight:800;\n    }\n    .copy-status { color:var(--green); font-size:.72rem; min-height:1em; }\n\n    footer {\n      padding:22px 0 50px;\n      color:#818782;\n      font-size:.76rem;\n    }\n\n    @media (max-width: 900px) {\n      .hero-grid { grid-template-columns:1fr; gap:24px; }\n      .hero-visual {\n        min-height:220px;\n        border-radius:18px;\n      }\n      .hero-visual img { min-height:220px; }\n      .ornament.top-right,\n      .ornament.badge-053 { display:none; }\n    }\n\n    @media (max-width: 800px) {\n      .sitebar-inner { min-height:58px; }\n      .location { display:none; }\n      .nav a:not(.inbox) { display:none; }\n      .hero { padding:30px 0 22px; }\n      .story-link {\n        grid-template-columns:minmax(0,1fr) 112px;\n        gap:13px;\n        align-items:start;\n        padding:17px 0;\n      }\n      .story-bullet { display:none; }\n      .story-thumb,\n      .story-thumb-placeholder {\n        width:112px;\n        height:84px;\n        max-width:none;\n        justify-self:end;\n        align-self:start;\n        order:initial;\n        border-radius:9px;\n      }\n      .story-title { font-size:1.22rem; }\n      .story-summary { max-width:100%; }\n      .signup { grid-template-columns:1fr; gap:15px; }\n      .signup-confirm { grid-column:1; margin-top:-7px; }\n      .tipbox { grid-template-columns:1fr; gap:12px; }\n    }\n\n    @media (max-width: 560px) {\n      .wrap { width:min(calc(100% - 24px),var(--max)); }\n      .brandlink { font-size:1.32rem; }\n      .nav .inbox { padding:8px 11px; }\n      .edition-title { font-size:clamp(2.6rem,13vw,4rem); }\n      .edition-intro { font-size:1rem; }\n      .hero-meta { font-size:.72rem; }\n      .feed-head { align-items:flex-start; flex-direction:column; gap:8px; }\n      .story-link {\n        gap:13px;\n        padding:16px 0;\n      }\n      .story-thumb,\n      .story-thumb-placeholder {\n        width:112px;\n        height:84px;\n        max-width:none;\n        justify-self:end;\n        align-self:start;\n        border-radius:9px;\n      }\n      .story-summary {\n        max-width:100%;\n        -webkit-line-clamp:2;\n      }\n      .signup-form { flex-direction:column; }\n      .signup-form .button { width:100%; }\n      .ornament.mid-left,\n      .ornament.bottom-right,\n      .ornament.badge-textiel { display:none; }\n    }\n  *{box-sizing:border-box}body{margin:0;background:#fbfaf6;color:#18241e;font:16px/1.65 system-ui,sans-serif}a{color:#155eef}header{border-bottom:1px solid #d8d4c8;background:#fffdf9}nav,main,footer{max-width:900px;margin:auto;padding:20px 24px}nav{display:flex;justify-content:space-between;align-items:center}.brand,h1,h2{font-family:Georgia,serif}.brand{font-size:26px;font-weight:bold}.pill{padding:6px 12px;background:#fff1dd;border-radius:20px;font-size:12px;font-weight:bold}.hero{padding:35px 0 25px}h1{font-size:clamp(36px,6vw,56px);line-height:1.08;letter-spacing:-1.5px;margin:12px 0 20px}.intro{font-size:19px;max-width:730px;color:#49584e}.meta,.where{color:#617066;font-size:13px}.jump{display:flex;flex-wrap:wrap;gap:10px;margin:24px 0}.jump a{border:1px solid #c6cfc7;border-radius:24px;padding:7px 16px;text-decoration:none;font-weight:600}.section-title{color:#226649;border-bottom:2px solid #b6c2b9;padding-bottom:10px;margin-top:38px;font-size:14px;letter-spacing:2px;text-transform:uppercase}article{border-bottom:1px solid #d8d4c8;padding:25px 0}h2{font-size:29px;line-height:1.2;margin:8px 0 10px}article p{max-width:760px;margin:12px 0}.tag{color:#155eef;font-size:12px;font-weight:750}.source{font-size:13px}details{font-size:13px;background:#f4eee1;border-radius:8px;padding:10px 14px;margin:15px 0}summary{cursor:pointer;font-weight:600}.editor{border:1px solid #dbcba6;padding:18px;border-radius:12px}.editor h2{font-size:23px}.quick{padding:20px;background:#edf3ee;border-radius:12px}.quick li{margin:9px 0}footer{color:#647268;font-size:13px}@media print{.jump,.editor,details,.pill{display:none}article{break-inside:avoid}body{background:white}nav{padding:10px 24px}}\nnav,main,footer{max-width:900px}header{position:sticky;top:0;z-index:10}.story-head{display:grid;grid-template-columns:minmax(0,1fr) 168px;gap:24px;align-items:start}.thumb{width:168px;height:116px;object-fit:cover;border-radius:11px;margin-top:8px;background:#e8e5dd}.credit{color:#717973}a:focus-visible,button:focus-visible,summary:focus-visible{outline:3px solid #155eef;outline-offset:4px}.topnav{font-size:13px;text-decoration:none;font-weight:700}.signup h2,.tipbox h2{font-size:25px}footer{padding-left:0;padding-right:0}article p{font-size:16px}.source{line-height:1.6}.tip-details summary{background:transparent}.tip-details[open]{grid-column:1/-1}.tip-form{width:100%}.tip-form label{font-size:14px}.tip-error[hidden]{display:none}#weten,#doen,#regelen,#meedoen{scroll-margin-top:90px}@media(max-width:600px){.story-head{grid-template-columns:minmax(0,1fr) 112px;gap:14px}.thumb{width:112px;height:84px}h2{font-size:24px}.brand{font-size:23px}nav{gap:12px}.topnav{font-size:12px}.source{font-size:12px}.intro{font-size:17px}}@media(max-width:370px){.story-head{grid-template-columns:minmax(0,1fr) 92px}.thumb{width:92px;height:76px}.brand{font-size:21px}}@media print{header{position:static}.thumb{width:120px;height:84px}.signup,.tipbox,.info{display:none}}\n[hidden]{display:none!important}body{background:#f6f1e7}.page-ornaments{z-index:0}.page-ornaments .ornament{opacity:.7}header,main{position:relative;z-index:2}header{position:sticky;background:rgba(251,250,246,.97)}main{max-width:1040px;background:rgba(255,253,249,.93);padding:0 36px 24px;border-left:1px solid #e1dbce;border-right:1px solid #e1dbce;box-shadow:0 18px 60px rgba(54,48,35,.035)}nav{max-width:1040px}.brand{font-size:30px;letter-spacing:-1px}.hero{padding:20px 0 24px;border-bottom:3px double #8e9a90}.edition-strip{display:flex;justify-content:space-between;gap:14px;border-top:3px double #1f3b2c;border-bottom:1px solid #929e93;padding:9px 0;margin-bottom:24px;font-size:11px;text-transform:uppercase;font-weight:750;letter-spacing:1.4px}.newspaper-hero{display:grid;grid-template-columns:minmax(0,1fr) 275px;gap:30px;align-items:center}.newspaper-hero h1{font-size:clamp(36px,4.5vw,54px);line-height:1.06;letter-spacing:-1.7px}.newspaper-hero .intro{font-size:17px;line-height:1.6}.edition-picture{margin:0;align-self:center}.edition-picture img{width:100%;height:auto;max-height:260px;object-fit:cover;border-radius:0 0 0 55px}.edition-picture figcaption{font-size:10px;color:#68776c;line-height:1.4;text-align:center;margin-top:10px}.jump{margin:24px 0 6px;gap:8px}.jump button{font:inherit;font-size:13px;font-weight:700;border:1px solid #c4ceca;border-radius:24px;padding:8px 18px;cursor:pointer;background:#fffdf9;color:#536359;transition:background .15s,color .15s}.jump button:hover{background:#eef3ff;color:#0c438f}.jump button.active{background:#155eef;color:white;border-color:#155eef}.filter-status{font-size:12px;color:#6b796e;margin-top:10px}.section-title{margin-top:30px;letter-spacing:2px;border-top:1px solid #9ca99d;border-bottom:1px solid #9ca99d;padding:9px 0;font-size:12px}.public-story h2{font-size:28px;letter-spacing:-.6px}.public-story{padding:23px 0}.quick{margin-top:32px;border-top:3px double #95a594;border-bottom:1px solid #95a594;border-radius:0;background:#f0f4ed}.quick h2{font-size:24px}.signup{margin-top:36px}.topnav{border:1px solid #b6c5db;border-radius:22px;padding:8px 14px}@media(min-width:1400px){.ornament.mid-left{left:calc((100vw - 1280px)/2)}.ornament.top-right{right:calc((100vw - 1320px)/2)}}@media(max-width:800px){main{margin:0 14px;padding:0 24px 20px}.newspaper-hero{grid-template-columns:minmax(0,1fr) 215px;gap:22px}.newspaper-hero h1{font-size:38px}.edition-picture img{border-radius:0 0 0 38px}.newspaper-hero .intro{font-size:16px}.brand{font-size:27px}}@media(max-width:600px){main{margin:0 10px;padding:0 18px 18px}.edition-strip{font-size:9px;letter-spacing:.8px;gap:8px;margin-bottom:18px}.newspaper-hero{grid-template-columns:1fr;gap:15px}.newspaper-hero h1{font-size:40px;letter-spacing:-1.2px}.edition-picture{display:flex;align-items:center;gap:16px}.edition-picture img{width:150px;height:100px;object-fit:cover;border-radius:0 0 0 30px}.edition-picture figcaption{text-align:left;font-size:11px;max-width:120px;margin:0}.jump button{font-size:12px;padding:7px 13px}.public-story h2{font-size:23px}.public-story p{font-size:15px}.brand{font-size:25px}.topnav{font-size:11px;padding:7px 10px}}@media print{main{border:0;box-shadow:none;max-width:none;margin:0}.edition-filters,.filter-status,.page-ornaments{display:none}.edition-strip{margin-top:0}.newspaper-hero{grid-template-columns:1fr 200px}header{position:static}}\n\n.newspaper-hero{grid-template-columns:minmax(0,1.05fr) minmax(0,.95fr);gap:28px;min-height:390px}.newspaper-hero h1{font-size:clamp(38px,4.2vw,51px)}.edition-picture{width:100%;align-self:center}.edition-picture img{width:100%;height:350px;max-height:none;object-fit:contain;border-radius:0 0 0 55px}.edition-picture figcaption{font-size:11px}.newspaper-hero .intro{max-width:440px}.public-story{display:grid;grid-template-columns:minmax(0,1fr) 230px;gap:24px;align-items:center;padding:18px 0}.public-story h2{font-size:25px;line-height:1.15;margin:5px 0 7px}.public-story h2 a{text-decoration:none;color:inherit}.public-story h2 a:hover{color:#0c438f}.public-story .where{font-size:12px;line-height:1.4}.public-story .card-summary{font-size:14px;line-height:1.5;margin:8px 0;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;max-width:100%}.card-bottom{display:flex;align-items:center;flex-wrap:wrap;gap:12px;margin-top:8px}.read-more{font-size:13px;font-weight:750;text-decoration:none}.read-more:hover{text-decoration:underline}.card-source{font-size:11px;color:#738074}.card-image{display:block;align-self:center}.public-story .thumb{display:block;width:230px;height:155px;margin:0;object-fit:cover}.card-copy{min-width:0}.detail-back{display:inline-block;font-size:13px;font-weight:700;text-decoration:none;margin:20px 0}.detail-title{font-family:Georgia,serif;font-size:clamp(32px,4vw,46px);line-height:1.12;margin:12px 0 18px}.detail-layout{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:32px;align-items:start}.detail-text p{font-size:17px;line-height:1.75;margin:0 0 18px}.detail-image{margin:0}.detail-image img{width:100%;height:230px;object-fit:cover;border-radius:12px}.detail-image figcaption{font-size:11px;color:#6e7b70;margin-top:8px}.detail-facts{border-top:1px solid #cbd3c9;border-bottom:1px solid #cbd3c9;padding:12px 0;margin:0 0 22px;color:#536258;font-size:13px}.detail-sources{border-top:3px double #9eaa9e;padding:20px 0;margin-top:24px;font-size:14px}.detail-sources h2{font-size:22px}.detail-related{border-top:1px solid #cbd3c9;padding:20px 0}.detail-related a{font-size:14px}.detail-related p{margin:8px 0}@media(max-width:800px){.newspaper-hero{grid-template-columns:1fr .9fr;gap:22px}.edition-picture img{height:310px}.public-story{grid-template-columns:minmax(0,1fr) 190px;gap:20px}.public-story .thumb{width:190px;height:140px}.detail-layout{grid-template-columns:1fr 240px;gap:24px}}@media(max-width:600px){.newspaper-hero{grid-template-columns:1fr;min-height:0;gap:10px}.edition-picture{display:block}.edition-picture img{width:100%;height:235px;object-fit:contain;border-radius:0}.edition-picture figcaption{text-align:center;max-width:none}.public-story{grid-template-columns:minmax(0,1fr) 126px;gap:14px;padding:16px 0;align-items:start}.public-story .thumb{width:126px;height:115px;margin-top:3px}.public-story h2{font-size:21px}.public-story .card-summary{font-size:13px;margin:6px 0}.public-story .tag{font-size:10px}.card-source{font-size:10px}.card-bottom{gap:5px 12px}.read-more{font-size:12px}.detail-layout{grid-template-columns:1fr}.detail-image{grid-row:1}.detail-image img{height:230px}.detail-title{font-size:34px}.detail-text p{font-size:16px}.detail-facts{font-size:12px}.brand{font-size:25px}}@media(max-width:370px){.brand{font-size:21px}.topnav{font-size:10px}.public-story{grid-template-columns:minmax(0,1fr) 104px;gap:12px}.public-story .thumb{width:104px;height:100px}.public-story h2{font-size:19px}.newspaper-hero h1{font-size:35px}}\n\n.newspaper-hero{align-items:center;min-height:0}.edition-picture{margin:0;width:100%}.edition-picture img{width:100%;height:auto;max-height:none;aspect-ratio:4/5;object-fit:contain;border-radius:0 0 0 48px}.edition-picture figcaption{margin-top:10px}@media(max-width:800px){.edition-picture img{height:auto;max-height:none}}@media(max-width:600px){.edition-picture{max-width:330px;justify-self:center}.edition-picture img{width:100%;height:auto;max-height:none;border-radius:0 0 0 34px}.newspaper-hero{gap:20px}.edition-picture figcaption{text-align:center}}\n'
ORNAMENTS = '<div class="page-ornaments" aria-hidden="true">\n    <div class="ornament top-right">\n      <svg width="170" height="170" viewBox="0 0 170 170" fill="none" xmlns="http://www.w3.org/2000/svg">\n        <circle cx="90" cy="86" r="56" fill="#EFE3C8"/>\n        <path d="M34 86c15-16 35-22 56-22 16 0 31-3 44-9" stroke="#D5B06B" stroke-width="2.5" stroke-linecap="round"/>\n        <path d="M47 110c18-8 39-12 64-12" stroke="#DAB97B" stroke-width="2.5" stroke-linecap="round"/>\n        <path d="M59 42c8 12 21 19 36 19" stroke="#C8D8CC" stroke-width="2.5" stroke-linecap="round"/>\n      </svg>\n    </div>\n\n    <div class="ornament mid-left">\n      <svg width="120" height="180" viewBox="0 0 120 180" fill="none" xmlns="http://www.w3.org/2000/svg">\n        <path d="M77 15c0 13-10 23-23 23S31 28 31 15 41 0 54 0s23 2 23 15Z" fill="#E9DFC8"/>\n        <path d="M41 56c13 9 30 9 43 0" stroke="#D5B06B" stroke-width="2.3" stroke-linecap="round"/>\n        <path d="M39 87c18-8 29-8 46 0" stroke="#D5B06B" stroke-width="2.3" stroke-linecap="round"/>\n        <path d="M34 117c22 13 35 13 56 0" stroke="#C3D8C8" stroke-width="2.3" stroke-linecap="round"/>\n        <circle cx="60" cy="153" r="18" fill="#F1E8D5"/>\n      </svg>\n    </div>\n\n    <div class="ornament bottom-right">\n      <svg width="165" height="145" viewBox="0 0 165 145" fill="none" xmlns="http://www.w3.org/2000/svg">\n        <rect x="22" y="24" width="98" height="80" rx="18" fill="#F1E8D5"/>\n        <path d="M39 78c11-11 22-16 39-16 16 0 32-4 45-13" stroke="#D4AE67" stroke-width="2.4" stroke-linecap="round"/>\n        <path d="M56 45v38" stroke="#C1D4C6" stroke-width="2.2" stroke-linecap="round"/>\n        <path d="M74 45v48" stroke="#C1D4C6" stroke-width="2.2" stroke-linecap="round"/>\n        <path d="M92 45v32" stroke="#C1D4C6" stroke-width="2.2" stroke-linecap="round"/>\n      </svg>\n    </div>\n\n    <div class="ornament badge-053">053</div>\n    <div class="ornament badge-textiel">textielstad</div>\n  </div>\n\n'

MONTHS = [
    "januari", "februari", "maart", "april", "mei", "juni",
    "juli", "augustus", "september", "oktober", "november", "december"
]
DAYS = [
    "maandag", "dinsdag", "woensdag", "donderdag",
    "vrijdag", "zaterdag", "zondag"
]


def esc(value):
    return html.escape(str(value or ""), quote=True)


def slugify(text):
    text = str(text or "").lower().strip()
    replacements = {
        "à": "a", "á": "a", "ä": "a", "â": "a",
        "è": "e", "é": "e", "ë": "e", "ê": "e",
        "ì": "i", "í": "i", "ï": "i", "î": "i",
        "ò": "o", "ó": "o", "ö": "o", "ô": "o",
        "ù": "u", "ú": "u", "ü": "u", "û": "u",
        "ç": "c", "ñ": "n", "’": "", "‘": "", "'": "",
        "&": " en "
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def human_date(date_string):
    day = dt.date.fromisoformat(date_string)
    return f"{DAYS[day.weekday()].capitalize()} {day.day} {MONTHS[day.month - 1]} {day.year}"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )


def request_json(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "BuurtDezeWeek/1.0 (+https://www.buurtdezeweek.nl/)"}
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


def download_file(url, destination):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "BuurtDezeWeek/1.0 (+https://www.buurtdezeweek.nl/)"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        destination.write_bytes(response.read())


def normalize_query(item, section_title):
    custom = (item.get("pixabay_query") or "").strip()
    if custom:
        return custom[:100]

    title = (item.get("title") or "").lower()
    label = (item.get("label") or "").lower()
    text = f"{title} {label}"

    mappings = [
        (("wegwerk", "verkeer", "asfalt", "straat"), "road construction neighborhood"),
        (("woning", "wonen", "huur", "nieuwbouw"), "housing neighborhood homes"),
        (("vrijwill",), "community volunteers helping"),
        (("film",), "cinema film audience"),
        (("jongeren", "huiskamer"), "young people community center"),
        (("wijkwijzer", "geld", "regelzaken"), "community help advice"),
        (("bodemdier", "regenworm", "pissebed"), "soil earthworm nature"),
        (("speeltuin", "kinderen"), "playground children neighborhood"),
        (("park", "wooldrik"), "city park trees neighborhood"),
        (("sport", "voetbal", "tennis"), "community sports field"),
        (("moskee", "islamitisch"), "mosque architecture"),
        (("school",), "school building education"),
        (("wijkbudget", "bewonersinitiatief"), "neighbors community meeting"),
    ]
    for needles, query in mappings:
        if any(needle in text for needle in needles):
            return query

    compact_title = re.sub(r"[^a-zA-ZÀ-ÿ0-9 ]+", " ", item.get("title") or "")
    compact_title = re.sub(r"\s+", " ", compact_title).strip()
    if compact_title:
        return (compact_title + " neighborhood community")[:100]
    return (section_title + " neighborhood community")[:100]


def old_item_map():
    if not OUTPUT_FILE.exists():
        return {}
    try:
        old = read_json(OUTPUT_FILE)
    except Exception:
        return {}

    result = {}
    for section in old.get("sections", []):
        for item in section.get("items", []):
            key = (item.get("url") or item.get("title") or "").strip()
            if key:
                result[key] = item
    return result


def image_identity(image_page_url="", image_url=""):
    """Maak een stabiele sleutel om dubbele afbeeldingen binnen één editie te voorkomen."""
    page = str(image_page_url or "").strip()
    if page:
        return f"page:{page.rstrip('/')}"
    url = str(image_url or "").strip()
    if url:
        return f"url:{url.split('?')[0]}"
    return ""


def remember_image(used_image_keys, image_page_url="", image_url=""):
    key = image_identity(image_page_url, image_url)
    if key:
        used_image_keys.add(key)


def get_pixabay_image(
    item,
    section_title,
    edition_date,
    slug,
    existing_item=None,
    used_image_keys=None,
):
    if used_image_keys is None:
        used_image_keys = set()

    manual_url = (item.get("image_url") or "").strip()
    if manual_url:
        manual_page_url = (item.get("image_page_url") or "").strip()
        manual_key = image_identity(manual_page_url, manual_url)

        if not manual_key or manual_key not in used_image_keys:
            remember_image(used_image_keys, manual_page_url, manual_url)
            if manual_url.startswith("https://cdn.pixabay.com/"):
                IMAGES_DIR.mkdir(parents=True, exist_ok=True)
                destination = IMAGES_DIR / f"{edition_date}-{slug}.jpg"
                try:
                    if not destination.exists() or (existing_item or {}).get("image_source_url") != manual_url:
                        download_file(manual_url, destination)
                    local_path = destination.relative_to(ROOT).as_posix()
                    return {"image_url": "/" + local_path, "image_path": local_path, "image_source_url": manual_url,
                            "image_credit": item.get("image_credit", ""), "image_page_url": manual_page_url,
                            "pixabay_query": item.get("pixabay_query") or normalize_query(item, section_title)}
                except Exception as exc:
                    print(f"Afbeelding blijft extern voor '{item.get('title')}': {exc}")
            return {
                "image_url": manual_url,
                "image_path": item.get("image_path", ""),
                "image_credit": item.get("image_credit", ""),
                "image_page_url": manual_page_url,
                "pixabay_query": item.get("pixabay_query") or normalize_query(item, section_title),
            }

        print(
            f"Dubbele handmatige afbeelding overgeslagen voor "
            f"'{item.get('title')}'"
        )

    if existing_item:
        image_url = (existing_item.get("image_url") or "").strip()
        image_path = (existing_item.get("image_path") or "").strip()
        image_page_url = (existing_item.get("image_page_url") or "").strip()
        existing_key = image_identity(image_page_url, image_url)

        if (
            image_path
            and (ROOT / image_path).exists()
            and (not existing_key or existing_key not in used_image_keys)
        ):
            remember_image(used_image_keys, image_page_url, image_url)
            return {
                "image_url": image_url or f"/{image_path}",
                "image_path": image_path,
                "image_credit": existing_item.get("image_credit", ""),
                "image_page_url": image_page_url,
                "pixabay_query": existing_item.get("pixabay_query") or normalize_query(item, section_title),
            }

    api_key = os.getenv("PIXABAY_API_KEY", "").strip()
    query = normalize_query(item, section_title)
    if not api_key:
        print(f"Geen PIXABAY_API_KEY: geen afbeelding voor {item.get('title')}")
        return {"pixabay_query": query}

    params = {
        "key": api_key,
        "q": query,
        "image_type": "photo",
        "orientation": "horizontal",
        "safesearch": "true",
        "per_page": 20,
        "min_width": 800,
    }
    api_url = "https://pixabay.com/api/?" + urllib.parse.urlencode(params)

    try:
        data = request_json(api_url)
    except Exception as exc:
        print(f"Pixabay-fout voor '{item.get('title')}': {exc}")
        return {"pixabay_query": query}

    hits = data.get("hits") or []
    if not hits:
        print(f"Geen Pixabay-resultaat voor '{query}'")
        return {"pixabay_query": query}

    unique_hits = []
    for candidate in hits:
        candidate_url = candidate.get("webformatURL") or candidate.get("largeImageURL") or ""
        candidate_key = image_identity(candidate.get("pageURL", ""), candidate_url)
        if candidate_key and candidate_key in used_image_keys:
            continue
        unique_hits.append(candidate)

    if not unique_hits:
        print(
            f"Alle Pixabay-resultaten voor '{query}' zijn al gebruikt in deze editie; "
            f"geen dubbele afbeelding geplaatst."
        )
        return {"pixabay_query": query}

    # Kies op populariteit/gebruik en gebruik resolutie alleen als laatste tie-breaker.
    # De oude code zette breedte op 1, waardoor een grote maar inhoudelijk zwakke foto
    # onbedoeld kon winnen.
    hit = max(
        unique_hits,
        key=lambda value: (
            int(value.get("likes") or 0),
            int(value.get("downloads") or 0),
            int(value.get("views") or 0),
            int(value.get("webformatWidth") or 0),
        )
    )

    source_url = hit.get("webformatURL") or hit.get("largeImageURL")
    if not source_url:
        return {"pixabay_query": query}

    selected_page_url = hit.get("pageURL", "")
    remember_image(used_image_keys, selected_page_url, source_url)

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{edition_date}-{slug}.jpg"
    destination = IMAGES_DIR / filename

    try:
        download_file(source_url, destination)
    except Exception as exc:
        print(f"Downloadfout Pixabay voor '{item.get('title')}': {exc}")
        return {
            "image_url": source_url,
            "pixabay_query": query,
            "image_credit": hit.get("user", ""),
            "image_page_url": selected_page_url,
        }

    relative_path = destination.relative_to(ROOT).as_posix()
    return {
        "image_url": f"/{relative_path}",
        "image_path": relative_path,
        "image_credit": hit.get("user", ""),
        "image_page_url": selected_page_url,
        "pixabay_query": query,
    }


def text_to_paragraphs(value):
    raw = str(value or "").strip()
    if not raw:
        return ""
    parts = [part.strip() for part in re.split(r"\n\s*\n", raw) if part.strip()]
    if not parts:
        parts = [raw]
    return "".join(f"<p>{esc(part)}</p>" for part in parts)


def build_article_page(edition, section, item):
    title = esc(item.get("title"))
    summary = esc(item.get("summary"))
    full_text = item.get("page_summary") or item.get("summary") or ""
    paragraphs = text_to_paragraphs(full_text)
    canonical = SITE_URL + "/" + item["page_url"].lstrip("/").removesuffix("index.html")
    image = ""
    if item.get("image_url"):
        image = (
            '<figure class="detail-image"><img src="' + esc(item["image_url"]) + '" alt="' +
            esc(item.get("image_alt") or "Illustratief beeld bij dit bericht") +
            '" width="640" height="430"><figcaption>Illustratief beeld. Geen foto van de beschreven locatie.' +
            ('<br><a href="' + esc(item["image_page_url"]) + '" target="_blank" rel="noopener">Beeld via Pixabay ↗</a>' if item.get("image_page_url") else '') +
            '</figcaption></figure>'
        )
    return (
        '<!doctype html><html lang="nl"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>' + title + ' | Buurt deze week</title><meta name="description" content="' + summary + '">'
        '<link rel="canonical" href="' + esc(canonical) + '"><style>' + DETAIL_CSS + '</style></head><body>' + ORNAMENTS +
        '<header><nav><a class="brand" href="/" style="text-decoration:none;color:inherit">Buurt deze week<span style="color:#155eef">.</span></a>'
        '<a class="topnav" href="/#inschrijven">In je mailbox →</a></nav></header><main>'
        '<a class="detail-back" href="/">← Terug naar de editie</a>'
        '<div class="edition-strip"><span>Donderdag-editie</span><span>' + esc(human_date(edition["date"])) + '</span><span>Zuidoost-Enschede</span></div>'
        '<article class="detail-article"><div class="tag">' + esc(section.get("title")) + '</div><h1 class="detail-title">' + title + '</h1>'
        '<div class="detail-facts"><strong>' + esc(item.get("display_date") or human_date(edition["date"])) + '</strong><br>' +
        esc(item.get("location") or item.get("label")) + '</div><div class="detail-layout"><div class="detail-text">' + paragraphs + '</div>' + image + '</div>'
        '<section class="detail-sources"><h2>Bron en meer informatie</h2><a href="' + esc(item.get("url")) + '" target="_blank" rel="noopener">' +
        esc(item.get("source")) + ' ↗</a><p>Onderdeel van de editie van ' + esc(human_date(edition["date"])) + '. Kijk bij de bron voor actuele informatie en eventuele wijzigingen.</p></section></article>'
        '<section class="detail-related"><a href="/berichten/">Bekijk alle berichten →</a></section>'
        '<footer>Buurt deze week · pilot Zuidoost-Enschede · <a href="/">Terug naar de editie</a></footer></main>'
        '<script async src="https://scripts.simpleanalyticscdn.com/latest.js"></script></body></html>'
    )


def build_articles_index(edition, sections):
    cards = []
    for section in sections:
        for item in section.get("items", []):
            image = ""
            if item.get("image_url"):
                image = f'<img src="{esc(item["image_url"])}" alt="" loading="lazy">'
            cards.append(f'''<article class="card">
              <a href="/{esc(item['page_url'])}">
                {image}
                <div class="body">
                  <div class="category">{esc(section.get('title'))}</div>
                  <h2>{esc(item.get('title'))}</h2>
                  <p>{esc(item.get('summary'))}</p>
                </div>
              </a>
            </article>''')

    return f'''<!doctype html>
<html lang="nl">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Berichten | Buurt deze week</title>
  <meta name="description" content="Alle berichten uit de editie van {esc(human_date(edition['date']))}.">
  <style>
    :root{{--bg:#f5f1e8;--paper:#fffdf8;--text:#18212b;--muted:#66707a;--line:#ded8cb;--blue:#155eef;--blue-dark:#0b3fa8;--radius:20px;--max:960px}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.55}}.wrap{{width:min(100% - 28px,var(--max));margin:0 auto;padding:28px 0 56px}}a{{color:inherit}}.back{{color:var(--blue-dark);font-weight:800;text-decoration:none}}h1{{font-family:Georgia,'Times New Roman',serif;font-size:clamp(2.4rem,7vw,4.8rem);line-height:1;letter-spacing:-.05em;margin:40px 0 10px}}.intro{{margin:0 0 28px;color:var(--muted);font-size:1.08rem}}.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}}.card{{background:var(--paper);border:1px solid rgba(88,78,54,.12);border-radius:var(--radius);overflow:hidden}}.card>a{{display:block;text-decoration:none;height:100%}}.card img{{display:block;width:100%;height:190px;object-fit:cover}}.body{{padding:20px}}.category{{font-size:.73rem;font-weight:900;text-transform:uppercase;letter-spacing:.06em;color:var(--blue);margin-bottom:8px}}h2{{font-size:1.28rem;line-height:1.15;letter-spacing:-.025em;margin:0 0 8px}}p{{margin:0;color:#4b5660;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}@media(max-width:680px){{.grid{{grid-template-columns:1fr}}}}
  </style>
</head>
<body><main class="wrap"><a class="back" href="/">← Terug naar de editie</a><h1>Alle berichten</h1><p class="intro">{esc(human_date(edition['date']))} · {len(cards)} berichten</p><div class="grid">{''.join(cards)}</div></main><script async src="https://scripts.simpleanalyticscdn.com/latest.js"></script></body></html>'''


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError("editie.json staat niet in de root van de repository")

    source = read_json(INPUT_FILE)
    if not source.get("edition", {}).get("date") or not isinstance(source.get("sections"), list):
        raise ValueError("editie.json heeft niet de verwachte structuur")

    edition = source["edition"]
    date_string = edition["date"]
    public = copy.deepcopy(source)
    previous = old_item_map()

    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)


    total = 0
    used_slugs = set()
    dt.date.fromisoformat(date_string)
    used_image_keys = set()

    for section in public["sections"]:
        for item in section.get("items", []):
            total += 1
            slug = (item.get("slug") or slugify(item.get("title"))).strip()
            if not slug:
                raise ValueError(f"Kon geen slug maken voor: {item.get('title')}")

            slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", slug)
            slug = slugify(slug)
            if not slug or slug in used_slugs:
                raise ValueError(f"Lege of dubbele slug: {slug}")
            used_slugs.add(slug)
            dated_slug = f"{date_string}-{slug}"
            article_dir = ARTICLES_DIR / dated_slug
            article_dir.mkdir(parents=True, exist_ok=True)
            item["slug"] = dated_slug
            item["page_url"] = f"berichten/{dated_slug}/index.html"
            item["page_summary"] = (item.get("page_summary") or item.get("summary") or "").strip()

            key = (item.get("url") or item.get("title") or "").strip()
            image_data = get_pixabay_image(
                item,
                section.get("title", ""),
                date_string,
                slug,
                previous.get(key),
                used_image_keys,
            )
            item.update({key: value for key, value in image_data.items() if value})

            page = build_article_page(edition, section, item)
            (article_dir / "index.html").write_text(page, encoding="utf-8")

    (ARTICLES_DIR / "index.html").write_text(
        build_articles_index(edition, public["sections"]),
        encoding="utf-8"
    )
    write_json(OUTPUT_FILE, public)

    print(f"Nieuwe editie gebouwd: {total} tussenpagina's")
    print("- editie-site.json")
    print("- berichten/index.html")
    print("- berichten/YYYY-MM-DD-slug/index.html")
    print("- assets/berichten/*")


if __name__ == "__main__":
    main()
