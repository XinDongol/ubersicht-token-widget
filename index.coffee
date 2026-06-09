command: "if [ -x ./.venv/bin/python ]; then ./.venv/bin/python ./ai_limits.py; else /usr/bin/env python3 ./ai_limits.py; fi"

refreshFrequency: "60s"

render: (output) -> output

style: """
  top: 38px
  right: 24px
  width: 344px
  color: #f5f7fb
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif
  pointer-events: none

  .panel
    box-sizing: border-box
    padding: 14px
    border-radius: 8px
    background: rgba(18, 21, 28, 0.78)
    border: 1px solid rgba(255, 255, 255, 0.14)
    box-shadow: 0 18px 48px rgba(0, 0, 0, 0.28)
    -webkit-backdrop-filter: blur(18px)

  .topline
    display: flex
    align-items: flex-start
    justify-content: space-between
    margin-bottom: 12px

  .topline p
    margin: 0 0 3px
    color: rgba(245, 247, 251, 0.58)
    font-size: 10px
    font-weight: 700
    text-transform: uppercase

  .topline h1
    margin: 0
    font-size: 17px
    font-weight: 750
    letter-spacing: 0

  .topline time
    color: rgba(245, 247, 251, 0.58)
    font-size: 11px
    font-variant-numeric: tabular-nums

  section
    padding-top: 12px
    margin-top: 12px
    border-top: 1px solid rgba(255, 255, 255, 0.1)

  section:first-of-type
    margin-top: 0

  .service-head
    display: flex
    align-items: center
    justify-content: space-between
    margin-bottom: 10px

  .service-head span
    font-size: 13px
    font-weight: 740

  .service-head b
    color: rgba(245, 247, 251, 0.74)
    font-size: 11px
    font-weight: 680
    text-transform: uppercase

  .subhead
    color: rgba(245, 247, 251, 0.58)
    font-size: 11px
    font-weight: 680
    margin: 0 0 8px

  .session-label
    margin-top: 14px

  .limit-row
    margin: 9px 0

  .limit-copy
    display: grid
    grid-template-columns: 128px 44px 1fr
    gap: 8px
    align-items: baseline
    margin-bottom: 5px
    font-size: 11px
    line-height: 1.2

  .limit-copy span
    color: rgba(245, 247, 251, 0.7)

  .limit-copy strong
    font-size: 13px
    font-weight: 780
    font-variant-numeric: tabular-nums

  .limit-copy em
    color: rgba(245, 247, 251, 0.52)
    font-size: 10px
    font-style: normal
    text-align: right

  .meter
    height: 6px
    overflow: hidden
    border-radius: 999px
    background: rgba(255, 255, 255, 0.13)

  .meter i
    display: block
    height: 100%
    min-width: 2px
    border-radius: 999px
    background: #4fdbc4

  .warn .meter i
    background: #f1c55f

  .danger .meter i
    background: #ff6f61

  .idle .meter i
    background: #8ea0b8

  .stats
    display: flex
    gap: 8px
    flex-wrap: wrap
    margin-top: 9px

  .stats span
    color: rgba(245, 247, 251, 0.62)
    font-size: 10px
    font-variant-numeric: tabular-nums

  .model-line
    margin-top: 6px
    color: rgba(245, 247, 251, 0.52)
    font-size: 10px
    white-space: nowrap
    overflow: hidden
    text-overflow: ellipsis

  .usage-table
    display: grid
    gap: 6px

  .usage-head,
  .usage-row
    display: grid
    grid-template-columns: 1fr 48px 48px 58px 58px
    gap: 6px
    align-items: baseline
    font-size: 11px

  .usage-head
    color: rgba(245, 247, 251, 0.5)

  .usage-row span
    color: rgba(245, 247, 251, 0.88)
    white-space: nowrap
    overflow: hidden
    text-overflow: ellipsis

  .usage-row b
    color: rgba(245, 247, 251, 0.62)
    font-weight: 650
    text-align: right
    font-variant-numeric: tabular-nums

  .usage-head span
    text-align: right
    white-space: nowrap

  .usage-head span:first-child
    text-align: left

  .usage-total
    display: flex
    justify-content: space-between
    color: rgba(245, 247, 251, 0.76)
    font-size: 11px
    font-variant-numeric: tabular-nums

  .usage-total strong
    font-size: 13px
    font-weight: 760

  .empty
    color: rgba(245, 247, 251, 0.58)
    font-size: 11px
"""
