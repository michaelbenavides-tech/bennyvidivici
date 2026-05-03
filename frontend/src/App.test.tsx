import { render } from '@testing-library/react'
import React from 'react'
import { describe, expect, it } from 'vitest'

describe('AI-SGP frontend', () => {
  it('renders a test node', () => {
    const view = render(<div>AI-SGP</div>)
    expect(view.getByText('AI-SGP')).toBeTruthy()
  })
})
