import { useRef, useCallback } from 'react'

interface Props {
  onResize: (delta: number) => void
}

export default function ResizeHandle({ onResize }: Props) {
  const dragging  = useRef(false)
  const lastX     = useRef(0)

  const onMouseMove = useCallback((e: MouseEvent) => {
    if (!dragging.current) return
    const delta = e.clientX - lastX.current
    lastX.current = e.clientX
    onResize(delta)
  }, [onResize])

  const onMouseUp = useCallback(() => {
    dragging.current = false
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    window.removeEventListener('mousemove', onMouseMove)
    window.removeEventListener('mouseup', onMouseUp)
  }, [onMouseMove])

  const onMouseDown = (e: React.MouseEvent) => {
    dragging.current = true
    lastX.current = e.clientX
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup', onMouseUp)
  }

  return (
    <div
      onMouseDown={onMouseDown}
      className="w-1 shrink-0 cursor-col-resize transition-colors duration-150 group relative"
      style={{ background: 'transparent' }}
    >
      <div
        className="absolute inset-y-0 -left-1 -right-1 group-hover:opacity-100 opacity-0 transition-opacity"
        style={{ background: 'rgba(0,61,165,0.25)' }}
      />
    </div>
  )
}