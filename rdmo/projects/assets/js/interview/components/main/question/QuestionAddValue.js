import React from 'react'
import PropTypes from 'prop-types'
import { maxBy, upperFirst } from 'lodash'

import { isDefaultValue } from '../../../utils/value'

const AddValue = ({ question, values, currentSet, disabled, createValue }) => {
  const defaultValue = values.find((value) => isDefaultValue(question, value))

  const handleClick = () => {
    const lastValue = maxBy(values, (v) => v.collection_index)
    const collectionIndex = lastValue ? lastValue.collection_index + 1 : 0

    createValue({
      attribute: question.attribute,
      set_prefix: currentSet.set_prefix,
      set_index: currentSet.set_index,
      set_collection: question.set_collection,
      collection_index: collectionIndex,
      unit: question.unit,
      value_type: question.value_type
    }, defaultValue)
  }

  return !disabled && !defaultValue?.pending && question.is_collection && (
    <button type="button" className="btn btn-success btn-xs add-value-button" onClick={handleClick}
            title={gettext('Add answer')} aria-label={gettext('Add answer')}>
      <i className="fa fa-plus fa-btn" aria-hidden="true"></i> {upperFirst(question.verbose_name)}
    </button>
  )
}

AddValue.propTypes = {
  question: PropTypes.object.isRequired,
  values: PropTypes.array.isRequired,
  currentSet: PropTypes.object.isRequired,
  disabled: PropTypes.bool.isRequired,
  createValue: PropTypes.func.isRequired
}

export default AddValue
