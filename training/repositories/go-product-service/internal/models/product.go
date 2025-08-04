package models

import (
	"time"

	"github.com/google/uuid"
)

// Product represents a product in the system
type Product struct {
	ID          uuid.UUID `json:"id" db:"id"`
	Name        string    `json:"name" db:"name" validate:"required,min=1,max=255"`
	Description string    `json:"description" db:"description" validate:"max=1000"`
	Price       float64   `json:"price" db:"price" validate:"required,gt=0"`
	Category    string    `json:"category" db:"category" validate:"required,max=100"`
	SKU         string    `json:"sku" db:"sku" validate:"required,max=50"`
	Stock       int       `json:"stock" db:"stock" validate:"gte=0"`
	IsActive    bool      `json:"is_active" db:"is_active"`
	CreatedAt   time.Time `json:"created_at" db:"created_at"`
	UpdatedAt   time.Time `json:"updated_at" db:"updated_at"`
}

// CreateProductRequest represents the request payload for creating a product
type CreateProductRequest struct {
	Name        string  `json:"name" validate:"required,min=1,max=255"`
	Description string  `json:"description" validate:"max=1000"`
	Price       float64 `json:"price" validate:"required,gt=0"`
	Category    string  `json:"category" validate:"required,max=100"`
	SKU         string  `json:"sku" validate:"required,max=50"`
	Stock       int     `json:"stock" validate:"gte=0"`
}

// UpdateProductRequest represents the request payload for updating a product
type UpdateProductRequest struct {
	Name        *string  `json:"name,omitempty" validate:"omitempty,min=1,max=255"`
	Description *string  `json:"description,omitempty" validate:"omitempty,max=1000"`
	Price       *float64 `json:"price,omitempty" validate:"omitempty,gt=0"`
	Category    *string  `json:"category,omitempty" validate:"omitempty,max=100"`
	SKU         *string  `json:"sku,omitempty" validate:"omitempty,max=50"`
	Stock       *int     `json:"stock,omitempty" validate:"omitempty,gte=0"`
	IsActive    *bool    `json:"is_active,omitempty"`
}

// ProductFilter represents filtering options for products
type ProductFilter struct {
	Category  string  `form:"category"`
	MinPrice  float64 `form:"min_price"`
	MaxPrice  float64 `form:"max_price"`
	IsActive  *bool   `form:"is_active"`
	Search    string  `form:"search"`
	Limit     int     `form:"limit,default=10" validate:"max=100"`
	Offset    int     `form:"offset,default=0"`
	SortBy    string  `form:"sort_by,default=created_at"`
	SortOrder string  `form:"sort_order,default=desc" validate:"oneof=asc desc"`
}
