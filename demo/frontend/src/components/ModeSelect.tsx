import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Box from '@mui/material/Box'
import CircularProgress from '@mui/material/CircularProgress'
import PhotoCamera from '@mui/icons-material/PhotoCamera'
import Timeline from '@mui/icons-material/Timeline'

type Props = {
  onSelect: (mode: 'single' | 'multi') => void
  loading: boolean
}

export default function ModeSelect({ onSelect, loading }: Props) {
  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        请选择使用模式
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        单图深挖围绕一张照片挖掘完整故事；多图叙事链可串联多张照片的人生故事。
      </Typography>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Button
          variant="outlined"
          size="large"
          fullWidth
          startIcon={<PhotoCamera />}
          onClick={() => onSelect('single')}
          disabled={loading}
          sx={{ py: 2, justifyContent: 'flex-start', textAlign: 'left' }}
        >
          <Box>
            <Typography fontWeight={600}>单图深挖</Typography>
            <Typography variant="body2" color="text.secondary">
              围绕一张照片：分析 → 访谈 → 生成该照片的故事
            </Typography>
          </Box>
        </Button>
        <Button
          variant="outlined"
          size="large"
          fullWidth
          startIcon={<Timeline />}
          onClick={() => onSelect('multi')}
          disabled={loading}
          sx={{ py: 2, justifyContent: 'flex-start', textAlign: 'left' }}
        >
          <Box>
            <Typography fontWeight={600}>多图叙事链</Typography>
            <Typography variant="body2" color="text.secondary">
              多张照片连续追问，串联跨越时间的人生故事，生成一篇连贯多图故事
            </Typography>
          </Box>
        </Button>
      </Box>
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
          <CircularProgress size={24} />
        </Box>
      )}
    </Paper>
  )
}
