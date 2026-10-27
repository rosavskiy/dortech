"use client";
import { useState } from "react";
import styles from "./Gallery.module.scss";

export function Gallery({ images }: { images: { url: string; alt: string }[] }) {
  const [i, setI] = useState(0);
  if (!images.length) return <div className={styles.empty}>Фото скоро</div>;
  const cur = images[Math.min(i, images.length - 1)];
  return (
    <div className={styles.wrap}>
      <div className={styles.main}><img src={cur.url} alt={cur.alt} width={1200} height={800} /></div>
      {images.length > 1 && (
        <div className={styles.thumbs}>
          {images.map((im, k) => (
            <button key={im.url} type="button" className={k === i ? styles.active : ""} onClick={() => setI(k)} aria-label={`Фото ${k + 1}`}>
              <img src={im.url} alt="" width={160} height={107} loading="lazy" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
