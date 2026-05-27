import { useEffect, useRef } from 'react'

const CHARS = '文学诗词歌赋经典传承离骚红楼梦滕王阁序屈原李白杜甫苏轼0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

export default function MatrixRain() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    let animationId

    const resize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    resize()
    window.addEventListener('resize', resize)

    const fontSize = 16
    const columns = Math.floor(canvas.width / fontSize)
    const drops = Array(columns).fill(1)
    let frameCount = 0

    const draw = () => {
      frameCount++
      // 每3帧才绘制一次，放慢流速
      if (frameCount % 3 !== 0) {
        animationId = requestAnimationFrame(draw)
        return
      }

      ctx.fillStyle = 'rgba(0, 0, 0, 0.05)'
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      ctx.font = `${fontSize}px "Noto Serif SC", monospace`

      for (let i = 0; i < drops.length; i++) {
        const char = CHARS[Math.floor(Math.random() * CHARS.length)]
        const x = i * fontSize
        const y = drops[i] * fontSize

        // 随机颜色：翠绿、金色、青色交替
        const colorChoice = Math.random()
        if (colorChoice < 0.6) {
          ctx.fillStyle = `rgba(0, 255, 70, ${0.8 + Math.random() * 0.2})`
        } else if (colorChoice < 0.8) {
          ctx.fillStyle = `rgba(218, 165, 32, ${0.7 + Math.random() * 0.3})`
        } else {
          ctx.fillStyle = `rgba(0, 255, 255, ${0.6 + Math.random() * 0.4})`
        }

        ctx.fillText(char, x, y)

        if (y > canvas.height && Math.random() > 0.975) {
          drops[i] = 0
        }
        drops[i]++
      }

      animationId = requestAnimationFrame(draw)
    }

    draw()

    return () => {
      cancelAnimationFrame(animationId)
      window.removeEventListener('resize', resize)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: 0,
      }}
    />
  )
}
