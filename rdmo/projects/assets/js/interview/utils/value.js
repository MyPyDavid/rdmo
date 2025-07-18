import { isNil, isEmpty, toString } from 'lodash'

import ValueFactory from '../factories/ValueFactory'

import { getChildPrefix } from './set'

const isDefaultValue = (question, value) => {
  if (isNil(value.id)) {
    if (question.default_text) {
      return question.default_text == value.text
    } else if (question.default_option) {
      return toString(question.default_option) == value.option
    } else if (question.default_external_id) {
      return question.default_external_id == value.external_id
    }
  }

  return false
}

const gatherDefaultValues = (page, values) => {
  const defaultValues = []

  if (!isNil(page) && !isNil(values)) {
    page.questions.forEach((question) => {
      values.filter((value) => (isNil(value.id) && (question.attribute === value.attribute))).forEach((value) => {
        if (isDefaultValue(question, value)) {
          defaultValues.push(value)
        }
      })
    })
  }

  return defaultValues
}

const initValues = (sets, values, element, setPrefix) => {
  if (isNil(setPrefix)) {
    setPrefix = ''
  }

  // loop over all sets of the current set prefix and the current element and over all questions
  sets.filter((set) => (
    (set.set_prefix === setPrefix) &&
    (set.element === element)
  )).forEach((set) => {
    element.elements.filter((e) => (e.model === 'questions.question')).forEach((question) => {
      // check if there is any value for this question and set
      if (isNil(values.find((value) => (
        (value.attribute === question.attribute) &&
        (value.set_prefix === set.set_prefix) &&
        (value.set_index === set.set_index)
      )))) {
        // if there is no value, create one, but not for checkboxes
        if (question.widget_type !== 'checkbox') {
          const value = ValueFactory.create({
            attribute: question.attribute,
            set_prefix: set.set_prefix,
            set_index: set.set_index,
            set_collection: question.set_collection,
            text: question.default_text,
            option: question.default_option,
            external_id: question.default_external_id
          })

          if (question.widget_type === 'range') {
            initRange(question, value)
          }

          values.push(value)
        }
      }
    })

    element.elements.filter((e) => (e.model === 'questions.questionset')).forEach((questionset) => {
      initValues(sets, values, questionset, getChildPrefix(set))
    })
  })
}

const initRange = (question, value) => {
  if (isEmpty(value.text)) {
    value.text = isNil(question.minimum) ? '0' : question.minimum
  }
}

const compareValues = (a, b, widget_type = null) => {
  if (isNil(a.id) || isNil(b.id)) {
    if (widget_type === 'checkbox') {
      return (a.attribute == b.attribute) &&
             (a.set_prefix == b.set_prefix) &&
             (a.set_index == b.set_index) &&
             (a.option == b.option)
    } else {
      return (a.attribute == b.attribute) &&
             (a.set_prefix == b.set_prefix) &&
             (a.set_index == b.set_index) &&
             (a.collection_index == b.collection_index)
    }
  } else {
    return a.id == b.id
  }
}

const isEmptyValue = (value) => {
  return isNil(value.id) || (
    isEmpty(value.text) && isNil(value.option) && isEmpty(value.external_id)
  )
}

export { isDefaultValue, gatherDefaultValues, initValues, initRange, compareValues, isEmptyValue }
