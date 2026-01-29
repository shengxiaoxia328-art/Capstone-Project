import { useEffect, useRef } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Collapse from '@mui/material/Collapse'
import ExpandMore from '@mui/icons-material/ExpandMore'
import ExpandLess from '@mui/icons-material/ExpandLess'

type Props = {
  lines: string[]
  /** 实时流式输出的文本（如模型逐字生成的故事），会显示在下方并随内容增长 */
  streamingText?: string
  open: boolean
  onToggle?: () => void
}

export default function ThinkingPanel({ lines, streamingText = '', open, onToggle }: Props) {
  const endRef = useRef<HTMLDivElement>(null)
  const hasContent = lines.length > 0 || streamingText.length > 0

  useEffect(() => {
    if (hasContent && open) endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [lines, streamingText, open, hasContent])

  if (!hasContent) return null

  return (
    <Box
      sx={{
        mt: 2,
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 2,
        overflow: 'hidden',
        bgcolor: 'grey.900',
        color: 'grey.300',
      }}
    >
      <Box
        component="button"
        onClick={onToggle}
        aria-expanded={open}
        aria-label={open ? '收起思考过程' : '展开思考过程'}
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          width: '100%',
          px: 2,
          py: 1,
          border: 'none',
          background: 'rgba(255,255,255,0.05)',
          color: 'grey.400',
          cursor: 'pointer',
          fontSize: '0.875rem',
          '&:hover': { background: 'rgba(255,255,255,0.08)' },
        }}
      >
        <Typography variant="caption" sx={{ fontWeight: 600 }}>
          思考过程
        </Typography>
        {open ? <ExpandLess sx={{ fontSize: 20 }} /> : <ExpandMore sx={{ fontSize: 20 }} />}
      </Box>
      <Collapse in={open}>
        <Box
          sx={{
            maxHeight: 220,
            overflow: 'hidden',
            px: 2,
            py: 1.5,
            fontFamily: 'ui-monospace, monospace',
            fontSize: '0.8125rem',
            lineHeight: 1.5,
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            display: 'flex',
            flexDirection: 'column',
            gap: 0.25,
          }}
        >
          {lines.map((line, i) => (
            <Box
              key={`${i}-${line.slice(0, 20)}`}
              component="span"
              sx={{
                display: 'block',
                animation: 'thinkingLineIn 0.25s ease-out',
                '@keyframes thinkingLineIn': {
                  '0%': { opacity: 0, transform: 'translateY(-4px)' },
                  '100%': { opacity: 1, transform: 'translateY(0)' },
                },
              }}
            >
              {line}
            </Box>
          ))}
          {streamingText && (
            <Box
              component="span"
              sx={{
                display: 'block',
                mt: lines.length > 0 ? 1 : 0,
                borderLeft: '2px solid',
                borderColor: 'primary.main',
                pl: 1.5,
                color: 'grey.200',
              }}
            >
              {streamingText}
              <Box
                component="span"
                sx={{
                  ml: 0.25,
                  opacity: 0.9,
                  animation: 'blink 0.8s step-end infinite',
                  '@keyframes blink': {
                    '50%': { opacity: 0 },
                  },
                }}
              >
                ▌
              </Box>
            </Box>
          )}
          <div ref={endRef} />
        </Box>
      </Collapse>
    </Box>
  )
}
